"""Provider-independent AI layer.

AI integration is fully optional: if no provider or API key is configured,
every AI feature reports that it is disabled. Commands and handlers treat the
service as a clean abstraction so the underlying provider can be replaced
without changing command logic.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from selfbot.config import Settings
from selfbot.utils.rate_limit import DailyUsageTracker

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 2


class AIError(Exception):
    """Raised when an AI provider request fails."""


class AIDisabledError(AIError):
    """Raised when AI is not configured/enabled."""


@dataclass
class AIResponse:
    text: str
    usage: int | None = None  # approximate token usage when known


@dataclass
class AIConfig:
    provider: str = ""
    api_key: str = ""
    model: str = ""
    api_base: str = ""
    enabled: bool = False
    prompt: str = "تو یک دستیار مفید هستی. پاسخ‌های کوتاه و مفید بده."
    context_length: int = 10
    max_tokens: int = 300
    temperature: float = 0.7
    cooldown: int = 5
    daily_limit: int = 50
    allowed_chats: list[int] = field(default_factory=list)
    blocked_chats: list[int] = field(default_factory=list)


class AIProvider(ABC):
    """Interface implemented by concrete AI providers."""

    name: str = ""

    @abstractmethod
    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(AIProvider):
    """Generic OpenAI-compatible chat-completions endpoint."""

    name = "openai"

    def __init__(self, api_key: str, model: str, api_base: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base or "https://api.openai.com/v1"
        self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or ""},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 300,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = await self._client.post(
                f"{self.api_base.rstrip('/')}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.RequestError as exc:
            raise AIError(f"provider request failed: {exc.__class__.__name__}") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIError("invalid provider response") from exc

    async def aclose(self) -> None:
        await self._client.aclose()


class AIService:
    """Facade over AI providers with usage limits and retries.

    The service is a no-op shell when AI is disabled — it never sends a request
    nor does it require an API key when disabled.
    """

    def __init__(
        self,
        config: AIConfig | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        self.config = config or AIConfig()
        self._provider = provider
        self._usage = DailyUsageTracker()

    @classmethod
    def from_settings(cls, settings: Settings) -> AIService:
        """Build an AIService from the application Settings object."""
        cfg = AIConfig(
            provider=settings.ai_provider,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            api_base=settings.ai_api_base,
            enabled=settings.ai_enabled,
            daily_limit=settings.ai_daily_limit,
            context_length=settings.ai_context_length,
            max_tokens=settings.ai_max_tokens,
            temperature=settings.ai_temperature,
        )
        provider: AIProvider | None = None
        if cfg.provider and cfg.api_key and cfg.model:
            provider = OpenAICompatibleProvider(cfg.api_key, cfg.model, cfg.api_base or None)
        service = cls(cfg, provider)
        return service

    @property
    def available(self) -> bool:
        return bool(self.config.enabled and self._provider is not None)

    def chat_allowed(self, chat_id: int) -> bool:
        if self.config.blocked_chats and chat_id in self.config.blocked_chats:
            return False
        return not (self.config.allowed_chats and chat_id not in self.config.allowed_chats)

    def can_use(self, key: str) -> bool:
        """Check the daily usage limit for a key."""
        if self.config.daily_limit <= 0:
            return True
        return self._usage.current(key) < self.config.daily_limit

    async def respond(self, message: str, *, context: str | None = None) -> AIResponse:
        """Generate a response for ``message``.

        Raises AIDisabledError when AI is not configured or enabled.
        """
        if not self.available:
            raise AIDisabledError("AI پیکربندی نشده است")

        provider = self._provider
        if provider is None:
            raise AIDisabledError("AI پیکربندی نشده است")

        system = self.config.prompt
        prompt = message if not context else f"{context}\n\nپیام کاربر: {message}"

        if not self.can_use("daily"):
            raise AIError("محدودیت استفاده روزانه به پایان رسیده است")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = await provider.complete(prompt, system=system)
            except AIError as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1.0 * (attempt + 1))
                continue
            self._usage.increment("daily")
            return AIResponse(text=result)
        raise AIError(f"پاسخ هوشمند دریافت نشد: {type(last_error).__name__}" if last_error else "خطای ناشناخته")

    async def aclose(self) -> None:
        if self._provider and hasattr(self._provider, "aclose"):
            await self._provider.aclose()  # type: ignore[attr-defined]


class FakeAIProvider(AIProvider):
    """Test-only provider that returns a fixed response."""

    name = "fake"

    def __init__(self, response: str = "پاسخ آزمایشی") -> None:
        self._response = response

    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        return self._response
