"""Input parsing and validation helpers."""

from __future__ import annotations

import re
from datetime import UTC, datetime

# Durations like "20m", "2h", "7d", "90s"
_DURATION_RE = re.compile(r"^\s*(\d+)\s*(s|sec|second|seconds|m|min|minute|minutes|h|hr|hour|hours|d|day|days|w|week|weeks)?\s*$", re.IGNORECASE)

_UNIT_FACTORS = {
    "s": 1, "sec": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
}


class ValidationError(Exception):
    """Raised when user input is invalid."""


def parse_duration(text: str) -> int:
    """Parse a human duration like ``20m`` into seconds.

    Also accepts bare numbers as seconds for convenience.
    """
    match = _DURATION_RE.match(text)
    if not match:
        raise ValidationError("duration format invalid")
    value = int(match.group(1))
    unit = (match.group(2) or "m").lower()
    return value * _UNIT_FACTORS[unit]


def parse_time_range(text: str) -> tuple[str, str]:
    """Parse ``HH:MM-HH:MM`` returning (start, end)."""
    parts = text.split("-")
    if len(parts) != 2:
        raise ValidationError("time range format invalid")
    start, end = parts[0].strip(), parts[1].strip()
    _validate_hhmm(start)
    _validate_hhmm(end)
    if start >= end:
        raise ValidationError("start must be before end")
    return start, end


def _validate_hhmm(value: str) -> None:
    if not re.fullmatch(r"\d{1,2}:\d{2}", value):
        raise ValidationError("time must be HH:MM")
    hours, minutes = (int(x) for x in value.split(":"))
    if hours > 23 or minutes > 59:
        raise ValidationError("time out of range")


def parse_hhmm(value: str) -> tuple[int, int]:
    """Parse ``HH:MM`` into (hours, minutes)."""
    _validate_hhmm(value)
    hours, minutes = (int(x) for x in value.split(":"))
    return hours, minutes


def parse_date_time(text: str) -> datetime:
    """Parse ``YYYY-MM-DD HH:MM`` into a naive datetime."""
    text = text.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValidationError("datetime format invalid")


def parse_absolute_datetime(text: str) -> datetime:
    """Parse an absolute date/time, returning timezone-aware UTC."""
    naive = parse_date_time(text)
    return naive.replace(tzinfo=UTC)


def is_valid_url(url: str, *, allow_http: bool = True) -> bool:
    """Basic URL validation (scheme + hostname)."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    schemes = {"http", "https"} if allow_http else {"https"}
    return parsed.scheme in schemes and bool(parsed.netloc)


def parse_int_list(text: str) -> tuple[float, str]:
    """Parse ``value unit`` like ``100 USD`` into (amount, unit)."""
    parts = text.strip().split()
    if len(parts) != 2:
        raise ValidationError("expected amount and unit")
    amount_text, unit = parts
    try:
        amount = float(amount_text)
    except ValueError as exc:
        raise ValidationError("amount is not a number") from exc
    return amount, unit.upper()


def humanize_seconds(seconds: float) -> str:
    """Format seconds as a short readable string."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m{seconds}s" if seconds else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h{minutes}m" if minutes else f"{hours}h"
    days, hours = divmod(hours, 24)
    return f"{days}d{hours}h" if hours else f"{days}d"
