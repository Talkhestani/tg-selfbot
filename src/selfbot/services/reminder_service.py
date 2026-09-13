"""Reminder scheduler backed by APScheduler."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from pytz import UTC as PYTZ_UTC
from sqlalchemy.ext.asyncio import AsyncSession

from selfbot.config import Settings
from selfbot.database.models import Reminder, ReminderType, utcnow
from selfbot.database.repository import ReminderRepository
from selfbot.messages import persian as msg
from selfbot.services.reminder_planner import compute_next_run, get_timezone

logger = logging.getLogger(__name__)

GRACE_SECONDS = 300  # fire missed one-time reminders within 5 minutes of downtime


class ReminderService:
    """Schedules reminder jobs and fires them through the Telegram client."""

    def __init__(
        self,
        client: Any,
        settings: Settings,
    ) -> None:
        self.client = client
        self.settings = settings
        # Scheduler runs in UTC; all DateTriggers receive aware-UTC datetimes.
        self.scheduler = AsyncIOScheduler(timezone=get_timezone("UTC"))
        self._jobs: dict[int, Any] = {}
        self._lock = asyncio.Lock()
        self._database: Any = None

    # -- lifecycle --------------------------------------------------------
    def start(self) -> None:
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def attach_database(self, database: Any) -> None:
        """Attach the database for job (re)scheduling across restarts."""
        self._database = database

    async def reschedule_all(self) -> None:
        """Drop all jobs and re-schedule from the database."""
        for job_id in list(self._jobs):
            self._remove_job(job_id)
        if self._database is None:
            return
        async with self._database.session_ctx() as session:
            repo = ReminderRepository(session)
            for reminder in await repo.list_active():
                await self.reschedule(reminder)

    # -- job management ---------------------------------------------------
    async def reschedule(self, reminder: Reminder) -> None:
        """Schedule (or update) the job for a single reminder."""
        async with self._lock:
            self._remove_job(reminder.id)
            try:
                run_at = compute_next_run(reminder.type.value, reminder.schedule, reminder.timezone)
            except Exception as exc:  # noqa: BLE001 - a broken rule must not stop the scheduler
                logger.warning("skipping reminder %s: %s", reminder.id, exc)
                return

            if reminder.type == ReminderType.ONE_TIME and run_at < utcnow():
                if (utcnow() - run_at).total_seconds() <= GRACE_SECONDS:
                    run_at = utcnow()
                else:
                    logger.info("one-time reminder %s was missed, skipping", reminder.id)
                    return
            elif reminder.type != ReminderType.ONE_TIME and run_at < utcnow():
                logger.info("recurring reminder %s had a past next-run, skipping", reminder.id)
                return

            try:
                job = self.scheduler.add_job(
                    self._fire,
                    trigger=DateTrigger(run_date=_as_utc_aware(run_at)),
                    args=[reminder.id],
                    id=f"reminder-{reminder.id}",
                    misfire_grace_time=600,
                    coalesce=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("could not schedule reminder %s: %s", reminder.id, exc)
                return
            self._jobs[reminder.id] = job
            await self._store_next_run(reminder.id, run_at)

    def _remove_job(self, reminder_id: int) -> None:
        job = self._jobs.pop(reminder_id, None)
        if job is not None:
            with contextlib.suppress(Exception):  # noqa: BLE001 - already gone
                self.scheduler.remove_job(job.id)

    async def _fire(self, reminder_id: int) -> None:
        if self._database is None:
            logger.error("database not attached to reminder service")
            return
        async with self._database.session_ctx() as session:
            repo = ReminderRepository(session)
            reminder = await repo.get(reminder_id)
            if reminder is None:
                return
            await self._deliver(session, reminder, repo)

    async def _deliver(self, session: AsyncSession, reminder: Reminder, repo: ReminderRepository) -> None:
        message_text = f"{msg.REMINDER_TRIGGERED}\n\n{reminder.text}"
        try:
            if reminder.chat_id:
                await self.client.send_message(reminder.chat_id, message_text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to deliver reminder %s: %s", reminder.id, exc.__class__.__name__)
            return

        if reminder.type == ReminderType.ONE_TIME:
            await repo.mark_done(reminder)
            self._remove_job(reminder.id)
            return

        # Recurring: recompute and re-schedule.
        await self.reschedule(reminder)

    async def _store_next_run(self, reminder_id: int, run_at: datetime) -> None:
        if self._database is None:
            return
        async with self._database.session_ctx() as session:
            stored = await session.get(Reminder, reminder_id)
            if stored is not None:
                stored.next_run_at = run_at
                await session.commit()


def _as_utc_aware(dt_naive_utc: datetime) -> datetime:
    """Attach the UTC timezone to a naive-UTC datetime for APScheduler."""
    return dt_naive_utc.replace(tzinfo=PYTZ_UTC)
