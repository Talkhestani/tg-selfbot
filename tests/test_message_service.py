"""Message service tests (delete by count / age / keyword)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from telethon.errors import FloodWaitError

from selfbot.services.message_service import MessageService


@dataclass
class FakeMessage:
    id: int
    text: str = ""
    date: datetime | None = None


class FakeClient:
    """Minimal stand-in for the Telethon client."""

    def __init__(self, messages: list[FakeMessage]) -> None:
        self._messages = sorted(messages, key=lambda m: m.id)
        self.deleted: list[list[int]] = []
        self.flood_once_ids: set[int] = set()
        self.always_fail = False
        self.search_supported = True
        self.search_calls = 0

    async def iter_messages(self, chat_id, limit=None, reverse=False, search=None, **kwargs):
        msgs = list(self._messages)
        if search is not None:
            self.search_calls += 1
            if not self.search_supported:
                raise RuntimeError("search not supported here")
            needle = search.lower()
            msgs = [m for m in msgs if needle in (m.text or "").lower()]
        ordered = msgs if reverse else msgs[::-1]
        for index, message in enumerate(ordered):
            if limit is not None and index >= limit:
                break
            yield message

    async def delete_messages(self, chat_id, ids):
        if isinstance(ids, int):
            ids = [ids]
        ids = list(ids)
        if self.always_fail:
            raise RuntimeError("cannot delete")
        for mid in ids:
            if mid in self.flood_once_ids:
                self.flood_once_ids.remove(mid)
                raise FloodWaitError(None, 0)
        self.deleted.append(ids)
        return [FakeMessage(id=mid) for mid in ids]


def _client_with(n: int, **kwargs) -> FakeClient:
    return FakeClient([FakeMessage(id=i + 1, text=f"msg {i + 1}") for i in range(n)], **kwargs)


async def test_delete_last_takes_newest_and_excludes_command() -> None:
    client = _client_with(10)
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_last(1, 3, exclude_ids=[10])
    assert result.deleted == 3
    assert result.errors == 0
    assert client.deleted == [[9, 8, 7]]


async def test_delete_last_chunks_over_100_ids() -> None:
    client = _client_with(250)
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_last(1, 250)
    assert result.deleted == 250
    assert result.errors == 0
    assert len(client.deleted) == 3
    assert sum(len(chunk) for chunk in client.deleted) == 250


async def test_delete_last_retries_after_flood_wait() -> None:
    client = _client_with(3)
    client.flood_once_ids = {3}
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_last(1, 3)
    assert result.deleted == 3
    assert result.errors == 0


async def test_delete_last_counts_permanent_failures() -> None:
    client = _client_with(4)
    client.always_fail = True
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_last(1, 4)
    assert result.deleted == 0
    assert result.errors == 4


async def test_delete_older_than_only_deletes_old() -> None:
    now = datetime.now(UTC)
    messages = [
        FakeMessage(id=1, text="old", date=now - timedelta(days=40)),
        FakeMessage(id=2, text="new", date=now - timedelta(days=1)),
        FakeMessage(id=3, text="old2", date=now - timedelta(days=31)),
    ]
    client = FakeClient(messages)
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_older_than(1, 30)
    assert result.deleted == 2
    assert client.deleted == [[3, 1]]


async def test_delete_by_keywords_uses_server_search() -> None:
    messages = [
        FakeMessage(id=1, text="hello world"),
        FakeMessage(id=2, text="nothing here"),
        FakeMessage(id=3, text="say hello again"),
    ]
    client = FakeClient(messages)
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_by_keywords(1, ["hello"])
    assert result.deleted == 2
    assert client.search_calls == 1
    assert client.deleted == [[3, 1]]


async def test_delete_by_keywords_falls_back_when_search_unsupported() -> None:
    messages = [
        FakeMessage(id=1, text="abc 123"),
        FakeMessage(id=2, text="no digits here!"),
    ]
    client = FakeClient(messages)
    client.search_supported = False
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_by_keywords(1, [r"\d+"], use_regex=True)
    assert result.deleted == 1
    assert client.deleted == [[1]]


async def test_delete_by_keywords_empty_list_deletes_nothing() -> None:
    client = _client_with(5)
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_by_keywords(1, [])
    assert result.deleted == 0
    assert client.deleted == []


class FloodTwiceClient(FakeClient):
    def __init__(self, messages: list[FakeMessage]) -> None:
        super().__init__(messages)
        self.attempts = 0

    async def delete_messages(self, chat_id, ids):
        self.attempts += 1
        raise FloodWaitError(None, 0)


async def test_delete_gives_up_after_repeated_flood() -> None:
    client = FloodTwiceClient([FakeMessage(id=1)])
    service = MessageService(client)  # type: ignore[arg-type]
    result = await service.delete_last(1, 1)
    assert result.deleted == 0
    assert result.errors == 1
