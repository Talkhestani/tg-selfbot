"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from selfbot.config import Settings


def _ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a sqlite database file."""
    if not database_url.startswith("sqlite"):
        return
    path = database_url.split("///")[-1]
    if not path or path == ":memory:":
        return
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def build_engine(database_url: str) -> AsyncEngine:
    """Create an async engine for the given SQLAlchemy URL."""
    _ensure_sqlite_parent(database_url)
    kwargs: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        kwargs["poolclass"] = NullPool
    return create_async_engine(database_url, future=True, **kwargs)


class Database:
    """Owns the engine and provides session factory."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = build_engine(settings.database_url)
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        return self.session_factory()

    @asynccontextmanager
    async def session_ctx(self) -> AsyncIterator[AsyncSession]:
        """Context manager yielding a scoped session."""
        async with self.session_factory() as session:
            yield session


def create_database(settings: Settings) -> Database:
    return Database(settings)
