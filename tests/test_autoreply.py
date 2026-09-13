"""Auto-reply matching and cooldown tests."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from selfbot.config import Settings
from selfbot.database.engine import Database
from selfbot.database.models import AutoReplyRule
from selfbot.database.repository import (
    AutoReplyRepository,
    ChatPermissionRepository,
    ConfigRepository,
)
from selfbot.services.autoreply_service import AutoReplyError, AutoReplyService, validate_rule
from selfbot.telegram.handlers.autoreply_handler import handle_incoming_auto_reply
from selfbot.telegram.permissions import PermissionService


def make_rule(
    pattern: str,
    response: str,
    match_type: str = "contains",
    priority: int = 0,
    enabled: bool = True,
    cooldown: int = 0,
) -> AutoReplyRule:
    return AutoReplyRule(
        pattern=pattern,
        response=response,
        match_type=match_type,
        priority=priority,
        enabled=enabled,
        cooldown=cooldown,
    )


def test_exact_match() -> None:
    service = AutoReplyService()
    rule = make_rule("سلام", "سلام!", "exact")
    response, matched = service.evaluate("سلام", [rule])
    assert response == "سلام!"
    assert matched is rule


def test_exact_no_match() -> None:
    service = AutoReplyService()
    rule = make_rule("سلام", "سلام!", "exact")
    response, _ = service.evaluate("سلام چطوری؟", [rule])
    assert response is None


def test_contains_match_case_insensitive() -> None:
    service = AutoReplyService()
    rule = make_rule("قیمت", "قیمت محصول X را بپرسید", "contains")
    response, _ = service.evaluate("قیمت محصول چیست؟", [rule])
    assert response == "قیمت محصول X را بپرسید"


def test_regex_match() -> None:
    service = AutoReplyService()
    rule = make_rule(r"\d+/+\d+", "این یک تاریخ است", "regex")
    response, _ = service.evaluate("تاریخ 1403/05/15", [rule])
    assert response == "این یک تاریخ است"


def test_invalid_regex_is_skipped() -> None:
    service = AutoReplyService()
    bad = make_rule(r"(", "خارجی", "regex")
    good = make_rule("سلام", "پاسخ درست", "contains")
    response, _ = service.evaluate("سلام", [bad, good])
    assert response == "پاسخ درست"


def test_disabled_rule_ignored() -> None:
    service = AutoReplyService()
    rule = make_rule("سلام", "خاموش", "contains", enabled=False)
    response, _ = service.evaluate("سلام", [rule])
    assert response is None


def test_priority_ordering() -> None:
    service = AutoReplyService()
    low = make_rule("سلام", "پاسخ کم اهمیت", "contains", priority=1)
    high = make_rule("سلام", "پاسخ پر اهمیت", "contains", priority=10)
    response, _ = service.evaluate("سلام بر شما", [low, high])
    assert response == "پاسخ پر اهمیت"


def test_empty_rules() -> None:
    service = AutoReplyService()
    response, matched = service.evaluate("هر چیزی", [])
    assert response is None
    assert matched is None


def test_cooldown_enforced() -> None:
    service = AutoReplyService()
    rule = make_rule("x", "پاسخ", "contains", cooldown=60)
    assert service.allows_cooldown(1, rule) is True
    assert service.allows_cooldown(1, rule) is False
    assert service.allows_cooldown(2, rule) is True  # different chat is fine


def test_chat_rate_limit() -> None:
    service = AutoReplyService()
    assert service.allow_chat_message(1) is True
    assert service.allow_chat_message(1) is False
    assert service.allow_chat_message(2) is True


def test_echo_detection() -> None:
    service = AutoReplyService()
    service.register_reply(1, "پاسخ من")
    assert service.looks_like_echo(1, "پاسخ من") is True
    assert service.looks_like_echo(1, "چیز دیگر") is False
    assert service.looks_like_echo(2, "پاسخ من") is False


def test_echo_expires() -> None:
    service = AutoReplyService(anti_loop_window=0)
    service.register_reply(1, "پاسخ")
    time.sleep(0.01)
    assert service.looks_like_echo(1, "پاسخ") is False


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.chat_id = 555  # private chat id (> 0)
        self.sender_id = 2  # not the owner
        self.replies: list[str] = []

    async def reply(self, text: str) -> None:
        self.replies.append(text)


async def test_repeats_keyword_replies_every_time(database: Database, settings: Settings) -> None:
    """A second 'سلام' in a private chat must be answered even when the rule
    response equals the keyword (regression: the old echo guard suppressed it).

    The chat is explicitly allowed by the owner, so the stranger is answered.
    """
    async with database.session_ctx() as session:
        await ConfigRepository(session).set_bool("autoreply_enabled", True)
        await ChatPermissionRepository(session).set_action(555, "allow")
        await AutoReplyRepository(session).add(
            AutoReplyRule(pattern="سلام", response="سلام", match_type="contains")
        )
    services = SimpleNamespace(
        permission=PermissionService(settings, database),
        database=database,
    )
    autoreply = AutoReplyService()

    first = _FakeMessage("سلام")
    second = _FakeMessage("سلام")
    await handle_incoming_auto_reply(first, services, autoreply)
    await handle_incoming_auto_reply(second, services, autoreply)

    assert first.replies == ["سلام"]
    assert second.replies == ["سلام"]


async def test_no_reply_to_stranger_pm(database: Database, settings: Settings) -> None:
    """A private chat that was not explicitly allowed gets no auto-reply."""
    async with database.session_ctx() as session:
        await ConfigRepository(session).set_bool("autoreply_enabled", True)
        await AutoReplyRepository(session).add(
            AutoReplyRule(pattern="سلام", response="سلام", match_type="contains")
        )
    services = SimpleNamespace(
        permission=PermissionService(settings, database),
        database=database,
    )
    autoreply = AutoReplyService()

    message = _FakeMessage("سلام")
    await handle_incoming_auto_reply(message, services, autoreply)

    assert message.replies == []


def test_validate_rule() -> None:
    validate_rule("سلام", "جواب", "exact")
    with pytest.raises(AutoReplyError):
        validate_rule("", "جواب", "exact")
    with pytest.raises(AutoReplyError):
        validate_rule("سلام", "", "exact")
    with pytest.raises(AutoReplyError):
        validate_rule("سلام", "جواب", "fuzzy")
    with pytest.raises(AutoReplyError):
        validate_rule("(", "جواب", "regex")
    with pytest.raises(AutoReplyError):
        validate_rule("x" * 2001, "جواب", "contains")
    with pytest.raises(AutoReplyError):
        validate_rule("سلام", "ج" * 4001, "contains")
