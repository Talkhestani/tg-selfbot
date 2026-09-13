"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from selfbot import app_context
from selfbot.config import Settings
from selfbot.database.engine import Database, create_database
from selfbot.database.models import Base


@pytest.fixture
def settings(tmp_path) -> Settings:
    db_path = tmp_path / "test.db"
    return Settings(
        api_id=123456,
        api_hash="0" * 32,
        session_name="test_session",
        database_url=f"sqlite+aiosqlite:///{db_path.as_posix()}",
        owner_id=1,
        timezone="Asia/Tehran",
    )


@pytest.fixture
async def database(settings: Settings) -> AsyncIterator[Database]:
    db = create_database(settings)
    app_context.init(db, settings)
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield db
    finally:
        app_context.reset()
        await db.dispose()


@pytest.fixture
async def session(database: Database):
    """Yield a scoped session without autocommit-on-exit model confusion."""
    async with database.session_ctx() as session:
        yield session
