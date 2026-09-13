"""Rate limiter, cooldown and daily usage tracker tests."""

from __future__ import annotations

import time

from selfbot.utils.rate_limit import (
    Bucket,
    CooldownTracker,
    DailyUsageTracker,
    RateLimiter,
)


def test_bucket_allows_until_empty() -> None:
    bucket = Bucket(capacity=3, refill_per_second=0)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False


def test_bucket_refill_over_time() -> None:
    bucket = Bucket(capacity=1, refill_per_second=100)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    time.sleep(0.02)
    assert bucket.try_acquire() is True


def test_ratelimiter_per_key_isolation() -> None:
    limiter = RateLimiter(default_times_per_minute=1000)
    limiter.set_limit("alpha", 1)
    assert limiter.allow("alpha") is True
    assert limiter.allow("alpha") is False
    # A different key uses its own default bucket.
    assert limiter.allow("beta") is True


def test_ratelimiter_default_bucket() -> None:
    limiter = RateLimiter(default_times_per_minute=1)
    assert limiter.allow("cmd") is True
    assert limiter.allow("cmd") is False


def test_cooldown_tracker() -> None:
    tracker = CooldownTracker()
    assert tracker.check_and_set("k", 30) is True
    assert tracker.check_and_set("k", 30) is False
    tracker.reset("k")
    assert tracker.check_and_set("k", 30) is True


def test_daily_usage_tracker() -> None:
    tracker = DailyUsageTracker()
    assert tracker.current("ai") == 0
    assert tracker.increment("ai") == 1
    assert tracker.increment("ai") == 2
    assert tracker.current("ai") == 2
    tracker.reset("ai")
    assert tracker.current("ai") == 0
