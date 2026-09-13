"""Data-access repositories, isolated from business logic."""

from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from selfbot.database.models import (
    AutoReplyRule,
    BioItem,
    BioTimeRule,
    ChatPermission,
    ConfigEntry,
    DownloadJob,
    ProfileBackup,
    Reminder,
    ReminderStatus,
    StopwatchState,
    TimerJob,
    utcnow,
)


class ConfigRepository:
    """Key-value application settings."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str, default: str = "") -> str:
        row = await self.session.get(ConfigEntry, key)
        return row.value if row else default

    async def set(self, key: str, value: str) -> None:
        row = await self.session.get(ConfigEntry, key)
        if row is None:
            self.session.add(ConfigEntry(key=key, value=value))
        else:
            row.value = value
        await self.session.commit()

    async def delete(self, key: str) -> None:
        await self.session.execute(delete(ConfigEntry).where(ConfigEntry.key == key))
        await self.session.commit()

    async def get_bool(self, key: str, default: bool = False) -> bool:
        value = await self.get(key)
        return value.lower() in {"1", "true", "yes", "on"} if value else default

    async def set_bool(self, key: str, value: bool) -> None:
        await self.set(key, "1" if value else "0")


class AutoReplyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[AutoReplyRule]:
        result = await self.session.execute(
            select(AutoReplyRule).order_by(AutoReplyRule.priority.desc(), AutoReplyRule.id)
        )
        return list(result.scalars().all())

    async def add(self, rule: AutoReplyRule) -> AutoReplyRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def get(self, rule_id: int) -> AutoReplyRule | None:
        return await self.session.get(AutoReplyRule, rule_id)

    async def delete(self, rule_id: int) -> bool:
        rule = await self.session.get(AutoReplyRule, rule_id)
        if rule is None:
            return False
        await self.session.delete(rule)
        await self.session.commit()
        return True


class ReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.status.in_([ReminderStatus.ACTIVE, ReminderStatus.PAUSED]))
            .order_by(Reminder.id)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder).where(Reminder.status != ReminderStatus.DELETED).order_by(Reminder.id)
        )
        return list(result.scalars().all())

    async def get(self, reminder_id: int) -> Reminder | None:
        return await self.session.get(Reminder, reminder_id)

    async def add(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def delete(self, reminder_id: int) -> bool:
        reminder = await self.session.get(Reminder, reminder_id)
        if reminder is None:
            return False
        await self.session.delete(reminder)
        await self.session.commit()
        return True

    async def mark_done(self, reminder: Reminder) -> None:
        reminder.status = ReminderStatus.DONE
        reminder.last_run_at = utcnow()
        await self.session.commit()


class BioTimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[BioTimeRule]:
        result = await self.session.execute(
            select(BioTimeRule).order_by(BioTimeRule.start_time, BioTimeRule.id)
        )
        return list(result.scalars().all())

    async def add(self, rule: BioTimeRule) -> BioTimeRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, rule_id: int) -> bool:
        rule = await self.session.get(BioTimeRule, rule_id)
        if rule is None:
            return False
        await self.session.delete(rule)
        await self.session.commit()
        return True


class BioItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[BioItem]:
        result = await self.session.execute(select(BioItem).order_by(BioItem.id))
        return list(result.scalars().all())

    async def add(self, text: str) -> BioItem:
        item = BioItem(text=text)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item_id: int) -> bool:
        item = await self.session.get(BioItem, item_id)
        if item is None:
            return False
        await self.session.delete(item)
        await self.session.commit()
        return True


class ChatPermissionRepository:
    """Allowed/blocked chat list."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_blocked(self, chat_id: int) -> bool:
        row = await self.session.get(ChatPermission, chat_id)
        return bool(row and row.action == "block")

    async def is_allowed(self, chat_id: int) -> bool:
        row = await self.session.get(ChatPermission, chat_id)
        return bool(row and row.action == "allow")

    async def set_action(self, chat_id: int, action: str) -> None:
        row = await self.session.get(ChatPermission, chat_id)
        if row is None:
            self.session.add(ChatPermission(chat_id=chat_id, action=action))
        else:
            row.action = action
        await self.session.commit()

    async def remove(self, chat_id: int) -> None:
        await self.session.execute(
            delete(ChatPermission).where(ChatPermission.chat_id == chat_id)
        )
        await self.session.commit()

    async def list_all(self) -> list[ChatPermission]:
        result = await self.session.execute(select(ChatPermission).order_by(ChatPermission.chat_id))
        return list(result.scalars().all())


class ProfileBackupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, backup: ProfileBackup) -> ProfileBackup:
        self.session.add(backup)
        await self.session.commit()
        await self.session.refresh(backup)
        return backup

    async def get(self, backup_id: int) -> ProfileBackup | None:
        return await self.session.get(ProfileBackup, backup_id)

    async def list_all(self, limit: int = 20) -> list[ProfileBackup]:
        result = await self.session.execute(
            select(ProfileBackup).order_by(ProfileBackup.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class TimerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, job: TimerJob) -> TimerJob:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_fired(self, job_id: int) -> None:
        await self.session.execute(
            update(TimerJob).where(TimerJob.id == job_id).values(status="fired")
        )
        await self.session.commit()

    async def list_pending(self) -> list[TimerJob]:
        result = await self.session.execute(
            select(TimerJob).where(TimerJob.status == "pending").order_by(TimerJob.fire_at)
        )
        return list(result.scalars().all())


class StopwatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> StopwatchState:
        result = await self.session.execute(select(StopwatchState).limit(1))
        state = result.scalar_one_or_none()
        if state is None:
            state = StopwatchState(running=False, accumulated=0)
            self.session.add(state)
            await self.session.commit()
            await self.session.refresh(state)
        return state

    async def save(self, state: StopwatchState) -> None:
        await self.session.commit()


class DownloadJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, job: DownloadJob) -> DownloadJob:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: int) -> DownloadJob | None:
        return await self.session.get(DownloadJob, job_id)

    async def update_status(
        self, job_id: int, status: str, *, error: str | None = None, file_path: str | None = None
    ) -> None:
        values: dict = {"status": status}
        if error is not None:
            values["error"] = error
        if file_path is not None:
            values["file_path"] = file_path
        await self.session.execute(update(DownloadJob).where(DownloadJob.id == job_id).values(**values))
        await self.session.commit()

class MessageBackupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, msg_id: int, chat_id: int, text: str) -> None:
        from selfbot.database.models import MessageBackup
        self.session.add(MessageBackup(message_id=msg_id, chat_id=chat_id, text=text))
        await self.session.commit()

    async def delete_by_chat_max(self, chat_id: int, max_id: int) -> int:
        from selfbot.database.models import MessageBackup
        from sqlalchemy import delete
        stmt = delete(MessageBackup).where(
            MessageBackup.chat_id == chat_id,
            MessageBackup.message_id <= max_id
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount
