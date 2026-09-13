"""Message management: bulk delete by count, age, and keyword."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 100
MAX_TOTAL_DELETE = 5000
DELETE_SLEEP = 0.5
FLOOD_SLEEP_CAP = 120
SCAN_MULTIPLIER = 10
SCAN_HARD_CAP = 20000


@dataclass
class DeleteResult:
    deleted: int
    errors: int = 0


class MessageService:
    """Deletes messages in a chat with safe batching and flood handling."""

    def __init__(self, client: TelegramClient) -> None:
        self.client = client

    # -- public API -----------------------------------------------------
    async def delete_last(
        self,
        chat_id: int,
        count: int,
        *,
        exclude_ids: tuple[int, ...] | list[int] = (),
        limit: int = MAX_TOTAL_DELETE,
    ) -> DeleteResult:
        """Delete the last ``count`` messages of a chat (newest first).

        Messages in ``exclude_ids`` (e.g. the command message itself) are
        skipped and do not count towards ``count``.
        """
        wanted = max(1, min(count, limit))
        excluded = set(exclude_ids)
        ids: list[int] = []
        async for message in self.client.iter_messages(chat_id, limit=wanted + len(excluded) + 1):
            if message.id in excluded:
                continue
            ids.append(message.id)
            if len(ids) >= wanted:
                break
        return await self._delete_collected(chat_id, ids)

    async def delete_older_than(
        self, chat_id: int, days: int, *, limit: int = MAX_TOTAL_DELETE
    ) -> DeleteResult:
        """Delete messages older than ``days`` (up to ``limit`` messages)."""
        cutoff = time.time() - max(1, days) * 86400
        ids: list[int] = []
        async for message in self.client.iter_messages(chat_id, reverse=False):
            if len(ids) >= limit:
                break
            date = getattr(message, "date", None)
            if date is None:
                continue
            if date.timestamp() >= cutoff:
                continue
            ids.append(message.id)
        return await self._delete_collected(chat_id, ids)

    async def delete_by_keywords(
        self,
        chat_id: int,
        keywords: list[str],
        *,
        limit: int = MAX_TOTAL_DELETE,
        use_regex: bool = False,
        case_insensitive: bool = True,
        match_all: bool = False,
        max_batch: int = DEFAULT_BATCH_SIZE,
    ) -> DeleteResult:
        """Delete messages matching keywords (up to ``limit`` messages)."""
        if not keywords:
            return DeleteResult(0)
        # Fast path: plain keywords can use Telegram's server-side search.
        if not use_regex and not (match_all and len(keywords) > 1):
            ids = await self._server_search_ids(chat_id, keywords, limit)
            if ids is not None:
                return await self._delete_collected(chat_id, ids)
        # Fallback: client-side scan with a bounded window.
        return await self._client_scan_delete(
            chat_id,
            keywords,
            limit=limit,
            use_regex=use_regex,
            case_insensitive=case_insensitive,
            match_all=match_all,
        )

    # -- search helpers ---------------------------------------------------
    async def _server_search_ids(
        self, chat_id: int, keywords: list[str], limit: int
    ) -> list[int] | None:
        """Collect matching ids via server-side search, or None on failure."""
        try:
            ids: list[int] = []
            seen: set[int] = set()
            for keyword in keywords:
                async for message in self.client.iter_messages(
                    chat_id, search=keyword, limit=limit
                ):
                    if len(ids) >= limit:
                        break
                    if message.id in seen:
                        continue
                    seen.add(message.id)
                    ids.append(message.id)
                if len(ids) >= limit:
                    break
            return ids
        except Exception as exc:  # noqa: BLE001 - fall back to client scan
            logger.info("server search unavailable in chat %s: %s", chat_id, exc.__class__.__name__)
            return None

    async def _client_scan_delete(
        self,
        chat_id: int,
        keywords: list[str],
        *,
        limit: int,
        use_regex: bool,
        case_insensitive: bool,
        match_all: bool,
    ) -> DeleteResult:
        patterns = self._compile_patterns(keywords, use_regex, case_insensitive)
        scan_cap = min(max(limit * SCAN_MULTIPLIER, limit + 200), SCAN_HARD_CAP)
        ids: list[int] = []
        async for message in self.client.iter_messages(chat_id, reverse=False, limit=scan_cap):
            if len(ids) >= limit:
                break
            text = message.text or ""
            hits = sum(1 for pattern in patterns if pattern.search(text))
            matched = (hits == len(patterns)) if match_all else (hits > 0)
            if matched:
                ids.append(message.id)
        return await self._delete_collected(chat_id, ids)

    @staticmethod
    def _compile_patterns(
        keywords: list[str], use_regex: bool, case_insensitive: bool
    ) -> list[re.Pattern[str]]:
        if use_regex:
            patterns: list[re.Pattern[str]] = []
            for keyword in keywords:
                try:
                    patterns.append(re.compile(keyword))
                except re.error as exc:
                    logger.warning("invalid regex %r skipped: %s", keyword, exc)
            return patterns
        flags = re.IGNORECASE if case_insensitive else 0
        return [re.compile(re.escape(keyword), flags) for keyword in keywords]

    # -- batched deletion ---------------------------------------------------
    async def _delete_collected(self, chat_id: int, ids: list[int]) -> DeleteResult:
        result = DeleteResult(0)
        for index in range(0, len(ids), DEFAULT_BATCH_SIZE):
            chunk = ids[index : index + DEFAULT_BATCH_SIZE]
            deleted, errors = await self._delete_chunk(chat_id, chunk)
            result.deleted += deleted
            result.errors += errors
            if index + DEFAULT_BATCH_SIZE < len(ids):
                await asyncio.sleep(DELETE_SLEEP)
        return result

    async def _delete_chunk(self, chat_id: int, ids: list[int]) -> tuple[int, int]:
        """Delete one batch; retry once after FloodWait, else go one-by-one."""
        try:
            await self.client.delete_messages(chat_id, ids)
            return len(ids), 0
        except FloodWaitError as exc:
            wait = min(exc.seconds + 1, FLOOD_SLEEP_CAP)
            logger.info("flood wait %ss while deleting in chat %s", exc.seconds, chat_id)
            await asyncio.sleep(wait)
            try:
                await self.client.delete_messages(chat_id, ids)
                return len(ids), 0
            except FloodWaitError as retry_exc:
                logger.warning(
                    "flood wait again (%ss), giving up batch of %d in chat %s",
                    retry_exc.seconds,
                    len(ids),
                    chat_id,
                )
                return 0, len(ids)
            except Exception as exc2:  # noqa: BLE001 - salvage one-by-one
                logger.warning(
                    "batch retry failed in chat %s: %s", chat_id, exc2.__class__.__name__
                )
        except Exception as exc:  # noqa: BLE001 - salvage one-by-one
            logger.warning("batch delete failed in chat %s: %s", chat_id, exc.__class__.__name__)
        return await self._delete_one_by_one(chat_id, ids)

    async def _delete_one_by_one(self, chat_id: int, ids: list[int]) -> tuple[int, int]:
        deleted = 0
        errors = 0
        for message_id in ids:
            try:
                await self.client.delete_messages(chat_id, [message_id])
                deleted += 1
            except FloodWaitError as exc:
                await asyncio.sleep(min(exc.seconds + 1, FLOOD_SLEEP_CAP))
                try:
                    await self.client.delete_messages(chat_id, [message_id])
                    deleted += 1
                except Exception:  # noqa: BLE001 - counted below
                    errors += 1
            except Exception:  # noqa: BLE001 - any delete failure is counted
                errors += 1
        return deleted, errors
