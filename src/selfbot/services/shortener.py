"""URL shortening with a replaceable provider abstraction."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from selfbot.utils.validators import is_valid_url

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 10.0


class ShortenerError(Exception):
    """Raised when the shortener cannot fulfil a request."""


class UrlShortener(ABC):
    """Provider interface for URL shortening."""

    @abstractmethod
    async def shorten(self, url: str) -> str:
        """Return a shortened URL for the given url."""
        raise NotImplementedError


class TinyUrlShortener(UrlShortener):
    """Shortener powered by https://tinyurl.com (no API key required)."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

    async def shorten(self, url: str) -> str:
        if not is_valid_url(url):
            raise ShortenerError("لینک معتبر نیست")
        try:
            response = await self._client.post(
                "https://tinyurl.com/api-create.php", data={"url": url}
            )
            response.raise_for_status()
            shortened = response.text.strip()
        except httpx.RequestError as exc:
            logger.warning("tinyurl request failed: %s", exc.__class__.__name__)
            raise ShortenerError("سرویس کوتاه‌کننده در دسترس نیست") from exc
        if not shortened.startswith(("http://", "https://")):
            raise ShortenerError("پاسخ نامعتبر از سرویس کوتاه‌کننده")
        return shortened


class KeyedUrlShortener(UrlShortener):
    """Shortener that uses an API key (e.g. T.ly or similar compatible APIs)."""

    def __init__(self, api_key: str, *, api_base: str = "https://api.t.ly/v1/shorten") -> None:
        self.api_key = api_key
        self.api_base = api_base
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

    async def shorten(self, url: str) -> str:
        if not is_valid_url(url):
            raise ShortenerError("لینک معتبر نیست")
        payload = {"long_url": url}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = await self._client.post(self.api_base, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except (httpx.RequestError, ValueError) as exc:
            logger.warning("shortener request failed: %s", exc.__class__.__name__)
            raise ShortenerError("سرویس کوتاه‌کننده در دسترس نیست") from exc
        result = data.get("short_url") or data.get("result") or data.get("url")
        if not result:
            raise ShortenerError("پاسخ نامعتبر از سرویس کوتاه‌کننده")
        return str(result)


class ShortenerFactory:
    """Builds the configured shortener implementation."""

    @staticmethod
    def create(api_key: str) -> UrlShortener:
        if api_key:
            return KeyedUrlShortener(api_key)
        return TinyUrlShortener()
