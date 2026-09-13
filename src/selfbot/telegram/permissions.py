"""Permission checks for commands and chats."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from selfbot.config import Settings
from selfbot.database.engine import Database
from selfbot.database.repository import ChatPermissionRepository, ConfigRepository

logger = logging.getLogger(__name__)


class PermissionDeniedError(Exception):
    """Raised when a user or chat is not allowed to run a command."""


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str = ""


class PermissionService:
    """Allowlist / blocklist / owner checks.

    The service opens its own database sessions, so it is safe to reuse across
    handlers without sharing session state.
    """

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self._database = database

    def is_owner(self, sender_id: int | None) -> bool:
        return self.settings.owner_id is not None and sender_id == self.settings.owner_id

    async def can_execute(self, sender_id: int | None, chat_id: int | None) -> PermissionDecision:
        """Check whether the sender may run commands in this chat."""
        if sender_id is None:
            return PermissionDecision(False, "شناسه فرستنده نامشخص است")

        if self.is_owner(sender_id):
            return PermissionDecision(True)

        # Non-owners are not allowed in PM by default (only the owner's
        # own messages are answered in private chats).
        if chat_id is None:
            return PermissionDecision(False, "این دستور فقط برای مالک قابل استفاده است")

        async with self._database.session_ctx() as session:
            repo = ChatPermissionRepository(session)
            if await repo.is_blocked(chat_id):
                return PermissionDecision(False, "این گفتگو اجازه استفاده از دستورات را ندارد")

            if self.settings.owner_id is not None:
                config = ConfigRepository(session)
                # When "owner-only" mode is on, even explicitly allowed chats
                # are rejected.
                if await config.get_bool("owner_only", False):
                    return PermissionDecision(False, "این دستور فقط برای مالک قابل استفاده است")
                allowed = await repo.is_allowed(chat_id)
                allowlist_mode = await config.get_bool("allowlist_enabled", False)
                if allowed:
                    return PermissionDecision(True)
                if allowlist_mode:
                    return PermissionDecision(False, "این گفتگو در لیست مجاز نیست")
                # Default: deny (only the owner or an explicitly allowed chat
                # may use commands).
                return PermissionDecision(False, "این دستور فقط برای مالک قابل استفاده است")

            # No owner_id configured: fall back to chat permissions.
            allowlist = await ConfigRepository(session).get_bool("allowlist_enabled", False)
            if allowlist and not await repo.is_allowed(chat_id):
                return PermissionDecision(False, "این گفتگو در لیست مجاز نیست")

        return PermissionDecision(True)

    async def can_respond_autoreply(self, chat_id: int | None) -> bool:
        """Whether auto-reply should react in this chat."""
        if chat_id is None:
            return True
        async with self._database.session_ctx() as session:
            repo = ChatPermissionRepository(session)
            return not await repo.is_blocked(chat_id)
