"""Offline smoke test: build services, register handlers, init schema.

Does not connect to Telegram.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from selfbot import app_context
from selfbot.config import Settings
from selfbot.database.engine import create_database
from selfbot.database.models import Base
from selfbot.services_container import Services
from selfbot.telegram.client import build_client
from selfbot.telegram.handlers import register_all


async def main() -> None:
    tmp = tempfile.mkdtemp()
    settings = Settings(
        api_id=123456,
        api_hash="0" * 32,
        session_name=str(Path(tmp) / "test.session"),
        database_url=f"sqlite+aiosqlite:///{Path(tmp).as_posix()}/test.db",
    )
    database = create_database(settings)
    app_context.init(database, settings)
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        client = build_client(settings)
        services = Services(client, settings, database)
        register_all(services.dispatcher, services)

        commands = services.dispatcher.commands
        assert commands, "no commands registered"
        names = sorted(cmd.name for cmd in commands.values())
        print(f"registered commands: {len(names)}")
        print(", ".join(names))
    finally:
        app_context.reset()
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(main())
