"""Stopwatch and timers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from telethon import TelegramClient

from selfbot.database.models import StopwatchState, TimerJob, utcnow
from selfbot.database.repository import StopwatchRepository, TimerRepository
from selfbot.messages import persian as msg

logger = logging.getLogger(__name__)


class StopwatchService:
    """One persistent stopwatch."""

    def __init__(self) -> None:
        pass

    async def start(self) -> str:

        async with _db_ctx() as ctx:
            session, database = ctx
            repo = StopwatchRepository(session)
            state = await repo.get()
            if state.running:
                return msg.STOPWATCH_STARTED
            state.running = True
            state.started_at = utcnow()
            state.accumulated = 0
            await repo.save(state)
        return msg.STOPWATCH_STARTED

    async def elapsed(self) -> int | None:
        async with _db_ctx() as ctx:
            session, _ = ctx
            repo = StopwatchRepository(session)
            state = await repo.get()
            return await self._elapsed_of(state)

    async def _elapsed_of(self, state: StopwatchState) -> int | None:
        if state.running and state.started_at is not None:
            return state.accumulated + int((utcnow() - state.started_at).total_seconds())
        return state.accumulated if not state.running else None

    async def stop(self) -> str | None:
        async with _db_ctx() as ctx:
            session, _ = ctx
            repo = StopwatchRepository(session)
            state = await repo.get()
            if not state.running:
                return None
            elapsed = await self._elapsed_of(state)
            state.running = False
            state.accumulated = int(elapsed or 0)
            state.started_at = None
            await repo.save(state)
            return msg.STOPWATCH_STOPPED.format(msg.format_duration(state.accumulated))

    async def reset(self) -> str:
        async with _db_ctx() as ctx:
            session, _ = ctx
            repo = StopwatchRepository(session)
            state = await repo.get()
            state.running = False
            state.started_at = None
            state.accumulated = 0
            await repo.save(state)
        return msg.STOPWATCH_RESET


class TimerService:
    """Persistent timers that fire a Telegram message."""

    def __init__(self, client: TelegramClient) -> None:
        self.client = client
        self._tasks: dict[int, asyncio.Task[Any]] = {}

    def start(self) -> None:
        """Schedule a background task to replay pending timers on restart."""
        self._replay_task = asyncio.create_task(self._replay_pending(), name="timer-replay")

    def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        if getattr(self, "_replay_task", None) is not None:
            self._replay_task.cancel()

    async def create(self, seconds: int, chat_id: int, reply_to: int | None = None) -> int:

        async with _db_ctx() as ctx:
            session, database = ctx
            repo = TimerRepository(session)
            job = TimerJob(
                duration=seconds,
                fire_at=utcnow() + timedelta(seconds=seconds),
                chat_id=chat_id,
                reply_to=reply_to,
            )
            created = await repo.add(job)
        self._tasks[created.id] = asyncio.create_task(
            self._wait_and_fire(created.id, seconds, chat_id, reply_to), name=f"timer-{created.id}"
        )
        return created.id

    async def _wait_and_fire(
        self, timer_id: int, seconds: int, chat_id: int, reply_to: int | None
    ) -> None:
        try:
            await asyncio.sleep(seconds)
            await self._fire(timer_id, chat_id, reply_to)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("timer %s failed: %s", timer_id, exc)

    async def _fire(self, timer_id: int, chat_id: int, reply_to: int | None) -> None:

        try:
            await self.client.send_message(chat_id, msg.TIMER_FINISHED, reply_to=reply_to)
        except Exception as exc:  # noqa: BLE001
            logger.warning("timer %s delivery failed: %s", timer_id, exc.__class__.__name__)
        async with _db_ctx() as ctx:
            session, _ = ctx
            await TimerRepository(session).mark_fired(timer_id)
        self._tasks.pop(timer_id, None)

    async def _replay_pending(self) -> None:

        await asyncio.sleep(1)
        async with _db_ctx() as ctx:
            session, _ = ctx
            repo = TimerRepository(session)
            pending = await repo.list_pending()
            for job in pending:
                remaining = (job.fire_at - utcnow()).total_seconds()
                if remaining <= 0:
                    continue
                self._tasks[job.id] = asyncio.create_task(
                    self._wait_and_fire(job.id, int(remaining), job.chat_id, job.reply_to),
                    name=f"timer-{job.id}",
                )


@asynccontextmanager
async def _db_ctx() -> AsyncIterator[tuple[Any, Any]]:
    """Yield (session, database) from the global database registry.

    The database is resolved lazily to avoid import cycles.
    """
    from selfbot.app_context import get_database

    database = get_database()
    session = database.session()
    try:
        yield session, database
    finally:
        await session.close()
