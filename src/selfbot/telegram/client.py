"""Telegram client construction."""

from __future__ import annotations

import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

from selfbot.proxy import first_proxy_dict

logger = logging.getLogger(__name__)


def build_client(settings) -> TelegramClient:  # type: ignore[no-untyped-def]
    """Create a TelegramClient configured from settings.

    Uses a file session by default, or a StringSession when SESSION_STRING is
    provided. Raises ValueError when API credentials are missing.
    """
    if not settings.api_id or not settings.api_hash:
        raise ValueError(
            "API_ID و API_HASH در فایل .env تنظیم نشده‌اند. "
            "از https://my.telegram.org دریافت کنید."
        )

    if settings.session_string:
        session = StringSession(settings.session_string)
        logger.info("using session string for %s", settings.session_name)
    else:
        session = settings.session_name

    proxy = first_proxy_dict()
    client = TelegramClient(
        session, settings.api_id, settings.api_hash, proxy=proxy
    )
    client.flood_sleep_threshold = 60
    return client


async def authenticate(client: TelegramClient, settings) -> None:  # type: ignore[no-untyped-def]
    """Start the client and authenticate interactively if needed."""
    await client.start()
    me = await client.get_me()
    logger.info("logged in as %s (@%s)", me.first_name, me.username or "بدون نام کاربری")
