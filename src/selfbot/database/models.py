"""SQLAlchemy ORM models for persistent application state."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def utcnow() -> datetime:
    """Current UTC time (naive, stored consistently)."""
    return datetime.now(UTC).replace(tzinfo=None)


class ReminderType(enum.StrEnum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReminderStatus(enum.StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"
    DELETED = "deleted"


class ConfigEntry(Base):
    """Simple key-value configuration persisted in the database."""

    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class AutoReplyRule(Base):
    """A keyword-based auto-reply rule."""

    __tablename__ = "autoreply_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="contains")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    cooldown: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Reminder(Base):
    """A scheduled reminder."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[ReminderType] = mapped_column(
        Enum(ReminderType, native_enum=False, length=16), nullable=False
    )
    schedule: Mapped[str] = mapped_column(String(128), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tehran")
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, native_enum=False, length=16), default=ReminderStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BioTimeRule(Base):
    """Time-based bio rule (e.g. 09:00-13:00 -> Working)."""

    __tablename__ = "bio_time_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    bio_text: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class BioItem(Base):
    """A stored bio used by the random-bio feature."""

    __tablename__ = "bio_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProfileBackup(Base):
    """A snapshot of the profile used for backup/restore."""

    __tablename__ = "profile_backups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_file_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChatPermission(Base):
    """Allow/block list entry for a chat."""

    __tablename__ = "chat_permissions"

    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class FilteredPattern(Base):
    """A keyword or regex pattern used by delete-by-keyword."""

    __tablename__ = "filtered_patterns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StopwatchState(Base):
    """Persisted stopwatch state (single row)."""

    __tablename__ = "stopwatch"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    running: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accumulated: Mapped[int] = mapped_column(Integer, default=0)


class TimerJob(Base):
    """A persisted timer."""

    __tablename__ = "timer_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    fire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    chat_id: Mapped[int] = mapped_column(Integer, default=0)
    reply_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DownloadJob(Base):
    """A download job queued through yt-dlp."""

    __tablename__ = "download_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Re-export models so `Base.metadata` includes them when imported.
__all__ = [
    "AutoReplyRule",
    "Base",
    "BioItem",
    "BioTimeRule",
    "ChatPermission",
    "ConfigEntry",
    "DownloadJob",
    "FilteredPattern",
    "ProfileBackup",
    "Reminder",
    "ReminderStatus",
    "ReminderType",
    "StopwatchState",
    "TimerJob",
]
