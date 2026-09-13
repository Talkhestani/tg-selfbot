"""Live financial rates from dastyar.io (currencies, gold, crypto)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_RATES_URL = "https://api.dastyar.io/express/financial-item?lang=fa"
_CACHE_TTL = 120  # seconds

_CATEGORY_ORDER = [
    ("currency", "💰 نرخ ارز"),
    ("gold", "🥇 طلا و سکه"),
    ("metal", "🥈 فلزات گرانبها"),
    ("crypto", "🪙 کریپتو"),
]

_CRYPTO_CAP = 10


class RatesError(Exception):
    """Raised when rates cannot be fetched or parsed."""


class RatesService:
    """Fetches and caches financial rates from dastyar.io."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=12, follow_redirects=False)
        self._cache: list[dict[str, Any]] = []
        self._cached_at: float = 0.0

    async def fetch(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._cache and now - self._cached_at < _CACHE_TTL:
            return self._cache
        try:
            response = await self._client.get(_RATES_URL)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RatesError("دریافت نرخ‌ها timeout شد") from exc
        except httpx.RequestError as exc:
            raise RatesError(f"دریافت نرخ‌ها ناموفق بود: {exc.__class__.__name__}") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise RatesError("پاسخ سرور JSON نامعتبر است") from exc
        if not isinstance(data, list) or not data:
            raise RatesError("داده نرخ‌ها خالی است")
        self._cache = list(data)
        self._cached_at = now
        return self._cache

    async def aclose(self) -> None:
        await self._client.aclose()


def format_rates(items: list[dict[str, Any]]) -> str:
    """Return a markdown-formatted snapshot of the current rates."""
    categories: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        cat = item.get("category") or "other"
        categories.setdefault(cat, []).append(item)
    for cat_list in categories.values():
        cat_list.sort(key=lambda x: int(x.get("sort_order") or 0))

    lines: list[str] = ["💹 نرخ‌های لحظه‌ای", ""]
    for cat_key, header in _CATEGORY_ORDER:
        group = categories.get(cat_key)
        if not group:
            continue
        if cat_key == "crypto":
            group = group[:_CRYPTO_CAP]
        lines.append(header)
        for item in group:
            lines.append(_render_line(item))
        lines.append("")

    lines.append("📊 منبع: dastyar.io")
    return "\n".join(lines)


def _render_line(item: dict[str, Any]) -> str:
    title = item.get("title") or item.get("enTitle") or ""
    price = _price_text(item)
    change = _change_text(item)
    return f"• {title}: **{price}** {change}".rstrip()


def _price_text(item: dict[str, Any]) -> str:
    raw = item.get("priceFloat") or item.get("price") or 0
    try:
        value = int(float(raw))
    except (ValueError, TypeError):
        value = 0
    currency = item.get("currency") or ""
    if currency == "تومان":
        return f"{value:,} تومان"
    return f"{value:,} {currency}" if currency else f"{value:,}"


def _change_text(item: dict[str, Any]) -> str:
    raw = item.get("change")
    try:
        ch = float(raw or 0)
    except (ValueError, TypeError):
        return ""
    if ch > 0:
        return f"⬆ {ch}٪"
    if ch < 0:
        return f"⬇ {abs(ch)}٪"
    return ""
