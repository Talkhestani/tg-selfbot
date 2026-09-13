"""Application service container (dependency wiring)."""

from __future__ import annotations

from pathlib import Path

from telethon import TelegramClient

from selfbot.config import Settings
from selfbot.database.engine import Database
from selfbot.services.ai_service import AIService
from selfbot.services.autoreply_service import AutoReplyService
from selfbot.services.converter import UnitConverter
from selfbot.services.currency import CurrencyService
from selfbot.services.downloader import DownloadService
from selfbot.services.message_service import MessageService
from selfbot.services.network import NetworkService
from selfbot.services.profile_service import ProfileAutomationService, ProfileService
from selfbot.services.random_tools import generate_password
from selfbot.services.rates import RatesService
from selfbot.services.reminder_service import ReminderService
from selfbot.services.screenshot import (
    PLAYWRIGHT_AVAILABLE,
    PlaywrightNotInstalledError,
    ScreenshotError,
    capture_screenshot,
)
from selfbot.services.shortener import ShortenerError, ShortenerFactory
from selfbot.services.time_tools import StopwatchService, TimerService
from selfbot.services.weather import WeatherError, create_weather_service
from selfbot.telegram.confirmation import ConfirmationManager
from selfbot.telegram.dispatcher import Dispatcher
from selfbot.telegram.permissions import PermissionService


class Services:
    """Aggregate of every service used by Telegram command handlers.

    Handlers access services as plain attributes; the container deliberately
    has no behaviour of its own.
    """

    def __init__(self, client: TelegramClient, settings: Settings, database: Database) -> None:
        self.client = client
        self.settings = settings
        self.database = database

        # Core infrastructure
        self.confirmation = ConfirmationManager()
        self.permission = PermissionService(settings, database)
        self.dispatcher = Dispatcher(
            client=client,
            services=self,
            confirmation=self.confirmation,
            permission=self.permission,
        )

        # Business services
        self.message_service = MessageService(client)
        self.autoreply_logic = AutoReplyService()
        self.reminder_service = ReminderService(client, settings)
        self.reminder_service.attach_database(database)
        self.downloader = DownloadService(client, settings)
        self.profile = ProfileService(client, settings)
        self.profile_automation = ProfileAutomationService(client, settings)
        self.profile_automation.attach_database(database)
        self.network = NetworkService()
        self.rates = RatesService()
        self.currency = CurrencyService()
        self.weather = create_weather_service(settings.weather_api_key)
        self.converter = UnitConverter()
        self.shortener = ShortenerFactory.create(settings.url_shortener_api_key)
        self.stopwatch = StopwatchService()
        self.timer = TimerService(client)
        self.screenshot = ScreenshotService()
        self.ai = AIService.from_settings(settings)

        # Expose pure functions used by handlers.
        self.generate_password = generate_password

    async def aclose(self) -> None:
        await self.network.aclose()
        await self.currency.aclose()
        await self.rates.aclose()
        await self.ai.aclose()


class ScreenshotService:
    """Thin wrapper isolating Playwright availability from handlers."""

    async def capture(self, url: str, output: Path) -> Path:
        return await capture_screenshot(url, output)

    @property
    def available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE


__all__ = [
    "Services",
    "PlaywrightNotInstalledError",
    "ScreenshotError",
    "ShortenerError",
    "WeatherError",
]
