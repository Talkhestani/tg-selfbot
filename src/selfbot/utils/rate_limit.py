"""Token-bucket style rate limiter."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class Bucket:
    """A single rate-limit bucket."""

    capacity: float
    refill_per_second: float
    tokens: float = 0.0
    updated_at: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def __post_init__(self) -> None:
        # Start the bucket full so the very first request is allowed.
        self.tokens = self.capacity

    @classmethod
    def times_per_minute(cls, times: int) -> Bucket:
        return cls(capacity=times, refill_per_second=times / 60.0)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until a token is available."""
        while True:
            async with self._lock:
                if self.try_acquire(tokens):
                    return
                wait = (tokens - self.tokens) / self.refill_per_second
            await asyncio.sleep(max(wait, 0.05))


class RateLimiter:
    """Per-key rate limiter, e.g. per command or per chat."""

    def __init__(self, default_times_per_minute: int = 30) -> None:
        self._default_times_per_minute = default_times_per_minute
        self._limits: dict[str, Bucket] = {}
        self._defaults: dict[str, Bucket] = {}

    def set_limit(self, key: str, times_per_minute: int) -> None:
        self._limits[key] = Bucket.times_per_minute(times_per_minute)

    def set_limit_custom(self, key: str, bucket: Bucket) -> None:
        self._limits[key] = bucket

    def _bucket_for(self, key: str) -> Bucket:
        bucket = self._limits.get(key)
        if bucket is not None:
            return bucket
        bucket = self._defaults.get(key)
        if bucket is None:
            bucket = Bucket.times_per_minute(self._default_times_per_minute)
            self._defaults[key] = bucket
        return bucket

    def allow(self, key: str, tokens: float = 1.0) -> bool:
        return self._bucket_for(key).try_acquire(tokens)

    async def wait(self, key: str, tokens: float = 1.0) -> None:
        await self._bucket_for(key).acquire(tokens)


class CooldownTracker:
    """Per-key cooldown tracking used by auto-reply."""

    def __init__(self) -> None:
        self._last: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def check_and_set(self, key: str, cooldown_seconds: float) -> bool:
        """Return True if allowed (not on cooldown), and mark the access."""
        now = time.monotonic()
        last = self._last.get(key, 0.0)
        if now - last >= cooldown_seconds:
            self._last[key] = now
            return True
        return False

    def reset(self, key: str) -> None:
        self._last.pop(key, None)


class DailyUsageTracker:
    """Simple daily usage counter, useful for AI usage limits."""

    def __init__(self) -> None:
        self._counts: dict[str, tuple[int, str]] = {}

    @staticmethod
    def _day() -> str:
        return time.strftime("%Y-%m-%d")

    def increment(self, key: str, amount: int = 1) -> int:
        day = self._day()
        count, stored_day = self._counts.get(key, (0, day))
        if stored_day != day:
            count = 0
            self._counts[key] = (0, day)
        count += amount
        self._counts[key] = (count, day)
        return count

    def current(self, key: str) -> int:
        day = self._day()
        count, stored_day = self._counts.get(key, (0, day))
        return count if stored_day == day else 0

    def reset(self, key: str, day: str | None = None) -> None:
        today = day or self._day()
        stored_day = self._counts.get(key, (0, today))[1]
        if stored_day == today:
            self._counts.pop(key, None)
