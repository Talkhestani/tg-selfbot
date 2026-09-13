"""Dispatcher routing tests: PM command silence, edit-based replies, cleanup."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from telethon.tl.types import Message

from selfbot.telegram.dispatcher import Dispatcher


class _FakePermission:
    def __init__(self, owner_id: int = 1) -> None:
        self.owner_id = owner_id

    def is_owner(self, sender_id: int | None) -> bool:
        return sender_id == self.owner_id

    async def can_execute(self, sender_id: int | None, chat_id: int | None) -> Any:
        allowed = sender_id == self.owner_id
        return SimpleNamespace(allowed=allowed, reason="" if allowed else "denied")


class _FakeConfirmation:
    def __init__(self, consume_text: str = "") -> None:
        self.consume_text = consume_text

    async def handle_incoming(
        self, chat_id: int, text: str, *, from_owner: bool = False
    ) -> bool:
        return bool(from_owner) and text.strip() == self.consume_text


class _FakeClient:
    def __init__(self) -> None:
        self.deleted: list[tuple[int, list[int]]] = []

    async def delete_messages(self, entity: int, ids: list[int]) -> None:
        self.deleted.append((entity, ids))


class _FakeMessage:
    def __init__(
        self,
        text: str,
        chat_id: int = 555,
        out: bool = False,
        sender_id: int = 2,
        msg_id: int = 7,
    ) -> None:
        self.text = text
        self.chat_id = chat_id
        self.out = out
        self.sender_id = sender_id
        self.id = msg_id


class _SpyDispatcher(Dispatcher):
    def __init__(
        self,
        services: Any,
        confirmation: Any,
        permission: Any,
        client: Any,
    ) -> None:
        super().__init__(client, services, confirmation, permission)
        self.scheduled: tuple[_FakeMessage, str] | None = None

    def _schedule_command(self, message: Message, body: str) -> None:
        self.scheduled = (message, body)  # type: ignore[assignment]


def _spy(command_prefix: str = "@") -> tuple[_SpyDispatcher, _FakeClient]:
    client = _FakeClient()
    services = SimpleNamespace(
        settings=SimpleNamespace(command_prefix=command_prefix),
        autoreply_logic=None,
    )
    dispatcher = _SpyDispatcher(
        services,
        _FakeConfirmation(),
        _FakePermission(),
        client,
    )
    return dispatcher, client


async def test_pm_at_message_from_stranger_is_ignored() -> None:
    dispatcher, _ = _spy()
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@help", chat_id=555, sender_id=2))
    )
    assert dispatcher.scheduled is None


async def test_pm_at_message_from_owner_is_processed() -> None:
    dispatcher, _ = _spy()
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@help", chat_id=555, sender_id=1))
    )
    assert dispatcher.scheduled is not None
    assert dispatcher.scheduled[1] == "help"


async def test_outgoing_command_is_processed() -> None:
    dispatcher, _ = _spy()
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@ping", chat_id=555, out=True, sender_id=1))
    )
    assert dispatcher.scheduled is not None
    assert dispatcher.scheduled[1] == "ping"


async def test_group_at_message_from_member_is_ignored() -> None:
    dispatcher, _ = _spy()
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@ping", chat_id=-100123, sender_id=2))
    )
    assert dispatcher.scheduled is None


async def test_group_at_message_from_owner_is_processed() -> None:
    dispatcher, _ = _spy()
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@ping", chat_id=-100123, sender_id=1))
    )
    assert dispatcher.scheduled is not None
    assert dispatcher.scheduled[1] == "ping"


async def test_group_at_message_from_allowed_member_is_processed() -> None:
    class _AllowAll(_FakePermission):
        async def can_execute(self, sender_id: int | None, chat_id: int | None) -> Any:
            return SimpleNamespace(allowed=True, reason="")

    dispatcher = _SpyDispatcher(
        SimpleNamespace(
            settings=SimpleNamespace(command_prefix="@"),
            autoreply_logic=None,
        ),
        _FakeConfirmation(),
        _AllowAll(),
        _FakeClient(),
    )
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("@ping", chat_id=-100123, sender_id=2))
    )
    assert dispatcher.scheduled is not None
    assert dispatcher.scheduled[1] == "ping"


async def test_pm_plain_message_goes_to_autoreply_path() -> None:
    dispatcher, _ = _spy()
    # autoreply_logic is None so the handler returns early without side effects.
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("سلام", chat_id=555, sender_id=2))
    )
    assert dispatcher.scheduled is None


async def test_confirmation_answer_of_owner_is_deleted() -> None:
    client = _FakeClient()
    services = SimpleNamespace(
        settings=SimpleNamespace(command_prefix="@"),
        autoreply_logic=None,
    )
    dispatcher = _SpyDispatcher(
        services,
        _FakeConfirmation(consume_text="بله"),
        _FakePermission(),
        client,
    )
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("بله", chat_id=555, out=True, sender_id=1, msg_id=9))
    )
    assert client.deleted == [(555, [9])]
    assert dispatcher.scheduled is None


async def test_confirmation_answer_of_stranger_is_not_deleted() -> None:
    client = _FakeClient()
    services = SimpleNamespace(
        settings=SimpleNamespace(command_prefix="@"),
        autoreply_logic=None,
    )
    dispatcher = _SpyDispatcher(
        services,
        _FakeConfirmation(consume_text="بله"),
        _FakePermission(),
        client,
    )
    await dispatcher._on_new_message(
        SimpleNamespace(message=_FakeMessage("بله", chat_id=555, out=False, sender_id=2, msg_id=9))
    )
    assert client.deleted == []
