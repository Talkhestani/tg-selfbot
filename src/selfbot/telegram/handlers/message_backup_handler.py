"""Silent message backup: save unseen messages; optionally purge on read."""
from __future__ import annotations

import logging

from telethon import events

from selfbot.config import Settings
from selfbot.database.engine import Database
from selfbot.database.repository import MessageBackupRepository

logger = logging.getLogger(__name__)


def register(client, settings: Settings, database: Database) -> None:
    if not settings.message_backup_enabled:
        return

    @client.on(events.NewMessage())
    async def _save(event):
        # Do not trigger read receipt; just save silently
        try:
            async with database.session() as sess:
                repo = MessageBackupRepository(sess)
                text = event.message.text or event.message.message or ""
                await repo.save(event.message.id, event.chat_id, text)
        except Exception:
            logger.exception("message backup save failed")

    @client.on(events.MessageRead(inbox=True))
    async def _purge_on_seen(event):
        if not settings.message_backup_remove_on_seen:
            return
        try:
            async with database.session() as sess:
                repo = MessageBackupRepository(sess)
                await repo.delete_by_chat_max(event.chat_id, event.max_id)
        except Exception:
            logger.exception("message backup purge failed")
