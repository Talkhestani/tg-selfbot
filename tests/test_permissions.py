"""PermissionService tests: owner-only default with explicit chat grants."""

from __future__ import annotations

from selfbot.config import Settings
from selfbot.database.engine import Database
from selfbot.database.repository import ChatPermissionRepository, ConfigRepository
from selfbot.telegram.permissions import PermissionService


def _service(settings: Settings, database: Database) -> PermissionService:
    return PermissionService(settings, database)


async def test_owner_always_allowed(settings: Settings, database: Database) -> None:
    service = _service(settings, database)
    assert (await service.can_execute(1, -100123)).allowed is True
    assert (await service.can_execute(1, None)).allowed is True


async def test_stranger_pm_is_denied(settings: Settings, database: Database) -> None:
    service = _service(settings, database)
    assert (await service.can_execute(2, None)).allowed is False


async def test_stranger_in_group_is_denied_by_default(
    settings: Settings, database: Database
) -> None:
    service = _service(settings, database)
    assert (await service.can_execute(2, -100123)).allowed is False


async def test_explicitly_allowed_chat_can_execute(
    settings: Settings, database: Database
) -> None:
    service = _service(settings, database)
    async with database.session_ctx() as session:
        await ChatPermissionRepository(session).set_action(-100123, "allow")
    assert (await service.can_execute(2, -100123)).allowed is True
    assert (await service.can_execute(2, None)).allowed is False


async def test_blocked_chat_is_denied_even_when_allowed_earlier(
    settings: Settings, database: Database
) -> None:
    service = _service(settings, database)
    async with database.session_ctx() as session:
        await ChatPermissionRepository(session).set_action(-100123, "block")
    assert (await service.can_execute(2, -100123)).allowed is False


async def test_owner_only_mode_rejects_allowed_chat(
    settings: Settings, database: Database
) -> None:
    service = _service(settings, database)
    async with database.session_ctx() as session:
        await ChatPermissionRepository(session).set_action(-100123, "allow")
        await ConfigRepository(session).set_bool("owner_only", True)
    assert (await service.can_execute(2, -100123)).allowed is False
    assert (await service.can_execute(1, -100123)).allowed is True


async def test_allowlist_mode_requires_allowed_chat(
    settings: Settings, database: Database
) -> None:
    service = _service(settings, database)
    async with database.session_ctx() as session:
        await ConfigRepository(session).set_bool("allowlist_enabled", True)
    assert (await service.can_execute(2, -100123)).allowed is False
    async with database.session_ctx() as session:
        await ChatPermissionRepository(session).set_action(-100123, "allow")
    assert (await service.can_execute(2, -100123)).allowed is True
