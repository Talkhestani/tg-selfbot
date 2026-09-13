"""Profile operations and automation for the owner account."""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime
from typing import Any

from telethon import TelegramClient
from telethon.tl import functions

from selfbot.config import Settings
from selfbot.database.repository import BioItemRepository, BioTimeRepository, ConfigRepository
from selfbot.services.reminder_planner import get_timezone
from selfbot.utils.validators import ValidationError, parse_hhmm

logger = logging.getLogger(__name__)

BIO_MAX_LENGTH = 70


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def validate_bio(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValidationError("بیو نمی‌تواند خالی باشد")
    if len(text) > BIO_MAX_LENGTH:
        raise ValidationError(f"بیو حداکثر {BIO_MAX_LENGTH} کاراکتر می‌تواند باشد")
    return text


class ProfileService:
    """One-time profile operations through the Telegram client."""

    def __init__(self, client: TelegramClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def set_bio(self, text: str) -> str:
        text = validate_bio(text)
        try:
            await self.client(functions.account.UpdateProfileRequest(about=text))
        except Exception as exc:  # noqa: BLE001
            raise ProfileError("تنظیم بیو انجام نشد") from exc
        return text


class ProfileAutomationService:
    """Periodic bio automation (clock, time-based, random)."""

    def __init__(self, client: TelegramClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self._tasks: list[asyncio.Task[Any]] = []
        self._stopping = False

    def start_tasks(self) -> None:
        self._stopping = False
        self._tasks = [
            asyncio.create_task(self._clock_loop(), name="bio-clock"),
            asyncio.create_task(self._name_clock_loop(), name="name-clock"),
            asyncio.create_task(self._autobio_loop(), name="auto-bio"),
        ]
        for task in self._tasks:
            task.add_done_callback(self._task_done)

    def _task_done(self, task: asyncio.Task[Any]) -> None:
        if not self._stopping and not task.cancelled():
            exc = task.exception()
            if exc is not None:
                logger.error("profile automation task failed: %s", exc)

    def shutdown(self) -> None:
        self._stopping = True
        for task in self._tasks:
            task.cancel()

    async def _clock_loop(self) -> None:
        tz = get_timezone(self.settings.timezone)
        while not self._stopping:
            try:
                enabled = await self._clock_enabled()
                if enabled:
                    now = datetime.now(tz=tz).strftime("%H:%M")
                    await self._apply_clock_bio(now)
                await asyncio.sleep(self.settings.bio_clock_interval)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("clock bio error: %s", exc)
                await asyncio.sleep(60)

    async def _apply_clock_bio(self, clock_text: str) -> None:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return
        async with database.session_ctx() as session:
            repo = BioTimeRepository(session)
            rules = await repo.list_all()
            active = None
            for rule in rules:
                if not rule.enabled:
                    continue
                if _time_in_range(rule.start_time, rule.end_time, clock_text):
                    active = rule
                    break
            if active is not None:
                await self.client(functions.account.UpdateProfileRequest(about=active.bio_text))
                return
            base = await self._base_bio()
            await self.client(functions.account.UpdateProfileRequest(about=f"{base} 🕐 {clock_text}"))

    async def _name_clock_loop(self) -> None:
        tz = get_timezone(self.settings.timezone)
        while not self._stopping:
            try:
                if await self._name_clock_enabled():
                    now = datetime.now(tz=tz).strftime("%H:%M")
                    await self._apply_clock_name(now)
                await asyncio.sleep(self.settings.bio_clock_interval)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("clock name error: %s", exc)
                await asyncio.sleep(60)

    async def _apply_clock_name(self, clock_text: str) -> None:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return
        async with database.session_ctx() as session:
            base = await ConfigRepository(session).get("base_first_name", "")
        if not base:
            return
        me = await self.client.get_me()
        last = me.last_name or ""
        target = f"{base} [{clock_text}]"
        try:
            await self.client(
                functions.account.UpdateProfileRequest(first_name=target, last_name=last)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("clock name update failed: %s", exc)

    async def _autobio_loop(self) -> None:
        while not self._stopping:
            try:
                if await self._autobio_enabled():
                    await self._apply_random_bio(force=False)
                await asyncio.sleep(max(self.settings.profile_update_interval * 10, 300))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("autobio error: %s", exc)
                await asyncio.sleep(300)

    async def _apply_random_bio(self, *, force: bool) -> bool:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return False
        async with database.session_ctx() as session:
            repo = BioItemRepository(session)
            items = await repo.list_all()
            if not items:
                return False
            bio = random.choice(items).text
            await self.client(functions.account.UpdateProfileRequest(about=bio))
            return True

    async def set_name_clock(self, enabled: bool) -> None:
        """Enable or disable the live time in the profile first name."""
        database: Any = getattr(self, "_database", None)
        if database is None:
            return
        if enabled:
            me = await self.client.get_me()
            first = me.first_name or ""
            last = me.last_name or ""
            base = _strip_clock_suffix(first)
            async with database.session_ctx() as session:
                await ConfigRepository(session).set("base_first_name", base)
                await ConfigRepository(session).set_bool("name_clock", True)
            tz = get_timezone(self.settings.timezone)
            now = datetime.now(tz=tz).strftime("%H:%M")
            target = f"{base} [{now}]"
        else:
            me = await self.client.get_me()
            last = me.last_name or ""
            async with database.session_ctx() as session:
                await ConfigRepository(session).set_bool("name_clock", False)
                base = await ConfigRepository(session).get("base_first_name", "")
            target = base or (me.first_name or "")
        try:
            await self.client(
                functions.account.UpdateProfileRequest(first_name=target, last_name=last)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("name clock set failed: %s", exc)

    # -- config helpers ---------------------------------------------------
    async def _clock_enabled(self) -> bool:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return False
        async with database.session_ctx() as session:
            return await ConfigRepository(session).get_bool("bio_clock", False)

    async def _name_clock_enabled(self) -> bool:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return False
        async with database.session_ctx() as session:
            return await ConfigRepository(session).get_bool("name_clock", False)

    async def _autobio_enabled(self) -> bool:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return False
        async with database.session_ctx() as session:
            return await ConfigRepository(session).get_bool("autobio", False)

    async def _base_bio(self) -> str:

        database: Any = getattr(self, "_database", None)
        if database is None:
            return ""
        async with database.session_ctx() as session:
            return await ConfigRepository(session).get("base_bio", "")

    def attach_database(self, database: Any) -> None:
        self._database = database


def _time_in_range(start: str, end: str, current: str) -> bool:
    start_h, start_m = parse_hhmm(start)
    end_h, end_m = parse_hhmm(end)
    cur_h, cur_m = parse_hhmm(current)
    start_min = start_h * 60 + start_m
    end_min = end_h * 60 + end_m
    cur_min = cur_h * 60 + cur_m
    return start_min <= cur_min <= end_min


def _strip_clock_suffix(first_name: str) -> str:
    """Remove a trailing `[HH:MM]` block left by the name clock."""
    import re

    return re.sub(r"\s*\[\d{1,2}:\d{2}\]\s*$", "", first_name).strip()
