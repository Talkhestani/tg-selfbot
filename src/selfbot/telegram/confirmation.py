"""Text-based confirmation flow for destructive actions."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from selfbot.messages import persian as msg

logger = logging.getLogger(__name__)

CONFIRM_TIMEOUT = 60
# NOTE: keep these in sync with the instruction text sent in ask()
# (CONFIRM_YES / CONFIRM_NO in messages.persian), otherwise users who copy
# the suggested answer would not match.
POSITIVE_KEYWORDS = {
    "بله",
    "تایید",
    "تأیید",
    "بلی",
    "آره",
    "yes",
    "y",
    "ok",
    "بله، تایید",
    "بله، تأیید",
    "بله تایید",
    "بله،تایید",
    "بله،تأیید",
}
NEGATIVE_KEYWORDS = {
    "خیر",
    "نه",
    "لغو",
    "انصراف",
    "no",
    "n",
    "خیر، انصراف",
    "خیر انصراف",
    "خیر،انصراف",
}


@dataclass
class _Pending:
    """A confirmation waiting for a reply."""

    chat_id: int
    event: asyncio.Event = field(default_factory=asyncio.Event)
    outcome: bool = False
    expires_at: float = 0.0


class ConfirmationManager:
    """Matches user replies to pending confirmations and awaits answers."""

    def __init__(self, timeout: int = CONFIRM_TIMEOUT) -> None:
        self._timeout = timeout
        self._pending: dict[int, _Pending] = {}
        self._lock = asyncio.Lock()

    @property
    def timeout(self) -> int:
        return self._timeout

    async def ask(
        self,
        chat_id: int,
        prompt: str,
        responder: Callable[[str], Awaitable[Any]],
        timeout_secs: int | None = None,
    ) -> bool:
        """Send a confirmation prompt and wait for the user's answer.

        Returns True on confirmation, False on rejection or timeout.
        """
        timeout = timeout_secs or self._timeout
        instructions = (
            f"{prompt}\n\n"
            f"برای تأیید پاسخ دهید: {msg.CONFIRM_YES}\n"
            f"برای لغو پاسخ دهید: {msg.CONFIRM_NO}\n\n"
            f"(انقضا در {timeout} ثانیه)"
        )
        await responder(instructions)

        async with self._lock:
            pending = _Pending(chat_id=chat_id, expires_at=time.monotonic() + timeout)
            self._pending[chat_id] = pending

        try:
            await asyncio.wait_for(pending.event.wait(), timeout=timeout)
            return pending.outcome
        except TimeoutError:
            logger.info("confirmation timed out in chat %s", chat_id)
            return False
        finally:
            async with self._lock:
                if self._pending.get(chat_id) is pending:
                    self._pending.pop(chat_id, None)

    async def handle_incoming(self, chat_id: int, text: str, *, from_owner: bool = False) -> bool:
        """Resolve a pending confirmation for the chat.

        Only answers sent by the owner (their own outgoing messages) are
        accepted — otherwise anyone typing "ok" in a group could confirm a
        destructive action. Returns True when the message was consumed.
        """
        if not from_owner:
            return False
        normalized = text.strip()
        async with self._lock:
            pending = self._pending.get(chat_id)
            if pending is None:
                return False
            if normalized.lower() in POSITIVE_KEYWORDS:
                pending.outcome = True
                pending.event.set()
                return True
            if normalized.lower() in NEGATIVE_KEYWORDS:
                pending.outcome = False
                pending.event.set()
                return True
        return False

    def has_pending(self, chat_id: int) -> bool:
        return chat_id in self._pending
