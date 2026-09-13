"""Application bootstrap: wires everything and runs the bot."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys

from selfbot import app_context
from selfbot.config import Settings, get_settings, load_dotenv_safe
from selfbot.database.engine import Database, create_database
from selfbot.database.models import Base
from selfbot.services_container import Services
from selfbot.telegram.client import TelegramClient, authenticate, build_client
from selfbot.telegram.handlers import register_all
from selfbot.telegram.handlers import message_backup_handler
from selfbot.utils.logging_cfg import setup_logging

logger = logging.getLogger(__name__)


class Application:
    """Owns the client, services and their lifecycle."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database: Database | None = None
        self.services: Services | None = None
        self.client: TelegramClient | None = None

    def prepare(self) -> None:
        """Create the database and the Telegram client."""
        self.database = create_database(self.settings)
        app_context.init(self.database, self.settings)
        self.client = build_client(self.settings)

    async def _init_schema(self) -> None:
        # Import models so metadata is complete before create_all.
        from selfbot.database import models  # noqa: F401

        database = self.database
        if database is None:
            raise RuntimeError("database not prepared")
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def run(self) -> None:
        self.prepare()

        settings = self.settings
        database = self.database
        client = self.client
        if database is None or client is None:
            raise RuntimeError("application not prepared")

        await self._init_schema()

        services = Services(client, settings, database)
        self.services = services

        register_all(services.dispatcher, services)
        message_backup_handler.register(client, settings, database)

        await authenticate(client, settings)

        # Auto-write owner ID to .env if missing so commands respond
        if not settings.owner_id:
            try:
                me = await client.get_me()
                if me.id:
                    from pathlib import Path
                    env_path = Path(".env")
                    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
                    new_lines = []
                    set_owner = False
                    for line in lines:
                        if line.startswith("OWNER_ID="):
                            new_lines.append(f"OWNER_ID={me.id}")
                            set_owner = True
                        else:
                            new_lines.append(line)
                    if not set_owner:
                        new_lines.append(f"OWNER_ID={me.id}")
                    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                    settings.owner_id = me.id
                    logger.info("owner_id set to %s in .env", me.id)
            except Exception:
                logger.exception("failed to auto-set owner_id")

        # Start periodic subsystems.
        await services.dispatcher.start()
        services.downloader.start()
        services.timer.start()
        services.profile_automation.start_tasks()
        services.reminder_service.start()
        await services.reminder_service.reschedule_all()

        logger.info("ربات با موفقیت شروع به کار کرد (مراقب خودت باش!)")
        await client.run_until_disconnected()

    async def close(self) -> None:
        logger.info("in shutdown")
        if self.services is not None:
            await self.services.dispatcher.stop()
            self.services.downloader.shutdown()
            self.services.timer.shutdown()
            self.services.profile_automation.shutdown()
            self.services.reminder_service.shutdown()
            await self.services.aclose()
        if self.client is not None:
            await self.client.disconnect()
        if self.database is not None:
            await self.database.dispose()
        app_context.reset()


async def _amain() -> None:
    load_dotenv_safe()
    settings = get_settings()
    setup_logging(settings)
    app = Application(settings)
    try:
        await app.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("received interrupt, shutting down")
    finally:
        await app.close()


def main() -> None:
    if sys.platform == "win32":
        # Telethon's connection layer relies on the selector event loop. Newer
        # Python versions warn about swapping the policy, so only do it on the
        # versions where the default is not already the selector loop.
        _set_windows_loop_policy()
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_amain())


def _set_windows_loop_policy() -> None:
    if sys.version_info >= (3, 14):
        return
    with contextlib.suppress(DeprecationWarning):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    main()
