"""Command handlers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from selfbot.telegram.dispatcher import Dispatcher


def register_all(dispatcher: Dispatcher, services: object) -> None:
    """Register every command handler on the dispatcher."""
    from selfbot.telegram.handlers import (
        autoreply_handler,
        calc_handler,
        convert_handler,
        download_handler,
        help_handler,
        message_handler,
        network_handler,
        profile_handler,
        reminder_handler,
        tool_handler,
    )

    help_handler.register(dispatcher, services)
    message_handler.register(dispatcher, services)
    autoreply_handler.register(dispatcher, services)
    reminder_handler.register(dispatcher, services)
    download_handler.register(dispatcher, services)
    tool_handler.register(dispatcher, services)
    network_handler.register(dispatcher, services)
    calc_handler.register(dispatcher, services)
    convert_handler.register(dispatcher, services)
    profile_handler.register(dispatcher, services)
