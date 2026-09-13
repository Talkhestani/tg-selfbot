"""Auto-reply business logic (keyword rules, cooldown, anti-loop)."""

from __future__ import annotations

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field

from selfbot.database.models import AutoReplyRule
from selfbot.utils.rate_limit import CooldownTracker

logger = logging.getLogger(__name__)

MATCH_TYPES = ("exact", "contains", "regex")


@dataclass
class AutoReplyConfig:
    enabled: bool = False
    default_response: str = ""


class AutoReplyError(Exception):
    """Raised when rule handling fails."""


@dataclass
class AutoReplyService:
    """Evaluates incoming messages against stored rules."""

    cooldown_tracker: CooldownTracker = field(default_factory=CooldownTracker)
    anti_loop_window: int = 60
    _recent_replies: dict[int, deque[tuple[str, float]]] = field(default_factory=dict)
    _chat_cooldown: CooldownTracker = field(default_factory=CooldownTracker)

    def evaluate(self, incoming: str, rules: list[AutoReplyRule]) -> tuple[str | None, AutoReplyRule | None]:
        """Return (response, matched_rule) for an incoming message.

        Rules are evaluated by priority (highest first); the first match wins.
        """
        if not rules:
            return None, None

        message = incoming.strip() if incoming else ""
        ordered = sorted(rules, key=lambda r: (r.priority, -(r.id or 0)), reverse=True)
        for rule in ordered:
            if not rule.enabled:
                continue
            if self._matches(message, rule):
                return rule.response, rule
        return None, None

    @staticmethod
    def _matches(message: str, rule: AutoReplyRule) -> bool:
        try:
            if rule.match_type == "exact":
                return message == rule.pattern
            if rule.match_type == "regex":
                return re.search(rule.pattern, message) is not None
            return rule.pattern.lower() in message.lower()
        except re.error as exc:
            logger.warning("invalid regex rule %s: %s", rule.id, exc)
            return False

    def allows_cooldown(self, chat_id: int, rule: AutoReplyRule) -> bool:
        """Return True when the per-chat cooldown for the rule has elapsed."""
        if rule.cooldown <= 0:
            return True
        return self.cooldown_tracker.check_and_set(
            f"rule:{rule.id}:chat:{chat_id}", float(rule.cooldown)
        )

    def allow_chat_message(self, chat_id: int, delay: float = 2.0) -> bool:
        """Global per-chat reply rate limiter to avoid a reply storm."""
        return self._chat_cooldown.check_and_set(f"chat:{chat_id}", delay)

    def register_reply(self, chat_id: int, text: str) -> None:
        """Remember a reply we just sent, used for echo detection."""
        history = self._recent_replies.setdefault(chat_id, deque(maxlen=10))
        history.append((text, time.monotonic()))

    def looks_like_echo(self, chat_id: int, text: str) -> bool:
        """True if the incoming message text matches a reply we recently sent."""
        now = time.monotonic()
        history = self._recent_replies.get(chat_id)
        if not history:
            return False
        normalized = text.strip().lower() if text else ""
        for reply_text, sent_at in history:
            if now - sent_at > self.anti_loop_window:
                continue
            if reply_text.strip().lower() == normalized:
                return True
        return False


def validate_rule(pattern: str, response: str, match_type: str) -> None:
    """Validate a rule's fields."""
    if not pattern.strip():
        raise AutoReplyError("کلیدواژه نمی‌تواند خالی باشد")
    if not response.strip():
        raise AutoReplyError("پاسخ نمی‌تواند خالی باشد")
    if match_type not in MATCH_TYPES:
        raise AutoReplyError("نوع تطبیق نامعتبر است")
    if match_type == "regex":
        try:
            re.compile(pattern)
        except re.error as exc:
            raise AutoReplyError(f"عبارت منظم نامعتبر است: {exc}") from exc
    if len(pattern) > 2000:
        raise AutoReplyError("کلیدواژه بیش از حد طولانی است")
    if len(response) > 4000:
        raise AutoReplyError("پاسخ بیش از حد طولانی است")
