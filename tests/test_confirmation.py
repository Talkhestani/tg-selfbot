"""Confirmation flow tests."""

from __future__ import annotations

import asyncio

from selfbot.telegram.confirmation import (
    CONFIRM_TIMEOUT,
    ConfirmationManager,
)


async def _ask_with_resolver(manager: ConfirmationManager, answer: str) -> bool:
    chat_id = 42
    responded = asyncio.Event()

    async def responder(text: str) -> None:
        responded.set()

    async def resolver() -> None:
        await responded.wait()
        await asyncio.sleep(0.05)  # let ask() register the pending item
        await manager.handle_incoming(chat_id, answer, from_owner=True)

    task = asyncio.create_task(manager.ask(chat_id, "ادامه می‌دهیم؟", responder))
    await asyncio.gather(task, resolver())
    return task.result()


async def test_positive_answer_confirms() -> None:
    assert await _ask_with_resolver(ConfirmationManager(), "بله") is True


async def test_negative_answer_cancels() -> None:
    assert await _ask_with_resolver(ConfirmationManager(), "نه") is False
    assert await _ask_with_resolver(ConfirmationManager(), "خیر") is False


async def test_keyword_match_is_case_insensitive() -> None:
    assert await _ask_with_resolver(ConfirmationManager(), "YES") is True


async def test_timeout_returns_false() -> None:
    manager = ConfirmationManager(timeout=1)

    async def responder(text: str) -> None:
        return None

    result = await manager.ask(123, "prompt", responder, timeout_secs=0.2)
    assert result is False
    assert manager.has_pending(123) is False


async def test_pending_is_cleared_after_resolution() -> None:
    manager = ConfirmationManager()
    chat_id = 7
    responded = asyncio.Event()

    async def responder(text: str) -> None:
        responded.set()

    async def resolver() -> None:
        await responded.wait()
        await asyncio.sleep(0.05)
        assert manager.has_pending(chat_id) is True
        await manager.handle_incoming(chat_id, "بله", from_owner=True)

    task = asyncio.create_task(manager.ask(chat_id, "p", responder))
    await asyncio.gather(task, resolver())
    assert manager.has_pending(chat_id) is False


def test_default_timeout() -> None:
    assert ConfirmationManager().timeout == CONFIRM_TIMEOUT


async def test_stranger_answer_is_ignored() -> None:
    """Answers from non-owners must never resolve a pending confirmation."""
    assert await _ask_with_resolver_non_owner("بله") is False
    assert await _ask_with_resolver_non_owner("ok") is False


async def _ask_with_resolver_non_owner(answer: str) -> bool:
    manager = ConfirmationManager()
    chat_id = 99
    responded = asyncio.Event()

    async def responder(text: str) -> None:
        responded.set()

    async def resolver() -> None:
        await responded.wait()
        await asyncio.sleep(0.05)
        # Stranger answer: must NOT resolve the pending item...
        consumed = await manager.handle_incoming(chat_id, answer)
        assert consumed is False
        # ...so ask() keeps waiting until it times out.
        await asyncio.sleep(0.05)

    task = asyncio.create_task(manager.ask(chat_id, "ادامه می‌دهیم؟", responder, timeout_secs=0.2))
    await asyncio.gather(task, resolver())
    return task.result()


async def test_instruction_phrases_are_accepted() -> None:
    """The exact phrases suggested in the prompt must work."""
    assert await _ask_with_resolver(ConfirmationManager(), "بله، تأیید") is True
    assert await _ask_with_resolver(ConfirmationManager(), "خیر، انصراف") is False
