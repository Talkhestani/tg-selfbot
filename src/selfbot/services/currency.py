"""Currency conversion with caching and error handling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import time

import httpx

HTTP_TIMEOUT = 12.0
CACHE_TTL_SECONDS = 3600


class CurrencyError(Exception):
    """Raised when a currency conversion cannot be performed."""


@dataclass(frozen=True)
class CurrencyConversion:
    amount: float
    from_currency: str
    to_currency: str
    rate: float
    result: float
    fetched_at: datetime


class CurrencyService:
    """Fetches live exchange rates via frankfurter.app and caches them."""

    _BASE_URL = "https://api.frankfurter.app/latest"

    def __init__(self, cache_ttl: int = CACHE_TTL_SECONDS) -> None:
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        self._cache_ttl = cache_ttl
        self._cache: dict[tuple[str, str], tuple[float, float]] = {}

    async def convert(self, amount: float, from_currency: str, to_currency: str) -> CurrencyConversion:
        src = from_currency.strip().upper()
        dst = to_currency.strip().upper()
        if not src or not dst:
            raise CurrencyError("کد ارز نامعتبر است")
        if src == dst:
            raise CurrencyError("ارز مبدأ و مقصد یکسان است")

        rate = await self._get_rate(src, dst)
        result = amount * rate
        return CurrencyConversion(
            amount=amount,
            from_currency=src,
            to_currency=dst,
            rate=rate,
            result=result,
            fetched_at=datetime.now(UTC),
        )

    async def _get_rate(self, src: str, dst: str) -> float:
        key = (src, dst)
        now = time()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self._cache_ttl:
            return cached[1]

        try:
            response = await self._client.get(self._BASE_URL, params={"from": src, "to": dst})
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as exc:
            raise CurrencyError("سرویس ارز در دسترس نیست") from exc
        except ValueError as exc:
            raise CurrencyError("پاسخ نامعتبر از سرویس ارز") from exc

        rates = data.get("rates") or {}
        if dst not in rates:
            raise CurrencyError(f"کد ارز «{dst}» شناخته نشد")
        rate = float(rates[dst])
        self._cache[key] = (now, rate)
        return rate

    async def aclose(self) -> None:
        await self._client.aclose()
