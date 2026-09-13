"""Reminder planning: pure functions for parsing and next-run computation.

Times are interpreted in the user's configured timezone and stored as naive
UTC internally, so they are timezone-stable across restarts.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from selfbot.utils.validators import ValidationError, parse_date_time, parse_duration

_WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def get_timezone(name: str | None) -> ZoneInfo:
    """Return a ZoneInfo for the given name, defaulting to UTC."""
    try:
        return ZoneInfo(name or "UTC")
    except (ValueError, KeyError):  # pragma: no cover - config-validated normally
        return ZoneInfo("UTC")


def now_utc() -> datetime:
    """Current naive UTC datetime."""
    return datetime.now(tz=ZoneInfo("UTC")).replace(tzinfo=None)


def _extract_reminder_text(text: str) -> str:
    """Return everything after the first whitespace-separated time token."""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def plan_relative_or_absolute(text: str, tz_name: str | None = None) -> tuple[str, str, datetime]:
    """Plan a one-time reminder.

    Supports absolute datetimes (``YYYY-MM-DD HH:MM <text>``, ``YYYY-MM-DD
    <text>`` or ``YYYY-MM-DD HH:MM:SS <text>``) and relative durations
    (``2h <text>``).

    Returns (reminder_text, schedule, next_run_utc_naive).
    """
    tz = get_timezone(tz_name)
    tokens = text.split()
    if not tokens:
        raise ValidationError("زمان معتبر نیست")

    # Absolute datetime first: try date+time (two tokens), then date-only.
    for size in (2, 1):
        if len(tokens) >= size:
            candidate = " ".join(tokens[:size])
            try:
                source = parse_date_time(candidate)
            except ValidationError:
                continue
            reminder_text = " ".join(tokens[size:])
            schedule = source.strftime("%Y-%m-%d %H:%M")
            aware = source.replace(tzinfo=tz)
            next_run = aware.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            if next_run <= now_utc() - timedelta(seconds=30):
                raise ValidationError("زمان یادآوری در گذشته است")
            return reminder_text, schedule, next_run

    # Relative duration: first token is the duration.
    first = tokens[0]
    reminder_text = " ".join(tokens[1:])
    try:
        seconds = parse_duration(first)
    except ValidationError:
        raise ValidationError("زمان معتبر نیست") from None
    future = datetime.now(tz=tz) + timedelta(seconds=seconds)
    next_run = future.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    schedule = next_run.strftime("%Y-%m-%d %H:%M")
    return reminder_text, schedule, next_run


def plan_daily(args: str, tz_name: str | None = None) -> tuple[str, str, datetime]:
    """Plan a daily reminder from ``HH:MM <text>``."""
    time_part, text = _split_time_text(args)
    hour, minute = _parse_hhmm(time_part)
    next_run = _next_daily(hour, minute, tz_name)
    return text, time_part, next_run


def plan_weekly(args: str, tz_name: str | None = None) -> tuple[str, str, datetime]:
    """Plan a weekly reminder from ``<weekday> HH:MM <text>``."""
    parts = args.split(maxsplit=2)
    if len(parts) < 3:
        raise ValidationError("قالب یادآوری هفتگی: mon 09:00 متن")
    day_token, time_part, text = parts
    weekday = _WEEKDAYS.get(day_token.lower())
    if weekday is None:
        raise ValidationError("روز هفته نامعتبر است")
    hour, minute = _parse_hhmm(time_part)
    next_run = _next_weekly(weekday, hour, minute, tz_name)
    return text, f"{day_token.lower()} {time_part}", next_run


def plan_monthly(args: str, tz_name: str | None = None) -> tuple[str, str, datetime]:
    """Plan a monthly reminder from ``<day-of-month> HH:MM <text>``."""
    parts = args.split(maxsplit=2)
    if len(parts) < 3:
        raise ValidationError("قالب یادآوری ماهانه: 1 10:00 متن")
    day_token, time_part, text = parts
    try:
        day_of_month = int(day_token)
    except ValueError:
        raise ValidationError("روز ماه نامعتبر است") from None
    if not 1 <= day_of_month <= 28:
        raise ValidationError("روز ماه باید بین ۱ تا ۲۸ باشد")
    hour, minute = _parse_hhmm(time_part)
    next_run = _next_monthly(day_of_month, hour, minute, tz_name)
    return text, f"{day_of_month} {time_part}", next_run


def compute_next_run(reminder_type: str, schedule: str, tz_name: str | None = None) -> datetime:
    """Recompute the next run of an existing reminder, returned as naive UTC."""
    if reminder_type == "one_time":
        naive = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
        return naive.replace(tzinfo=None)
    if reminder_type == "daily":
        hour, minute = _parse_hhmm(schedule)
        return _next_daily(hour, minute, tz_name)
    if reminder_type == "weekly":
        day_token, time_part = schedule.split(maxsplit=1)
        hour, minute = _parse_hhmm(time_part)
        return _next_weekly(_WEEKDAYS[day_token.lower()], hour, minute, tz_name)
    if reminder_type == "monthly":
        day_token, time_part = schedule.split(maxsplit=1)
        hour, minute = _parse_hhmm(time_part)
        return _next_monthly(int(day_token), hour, minute, tz_name)
    raise ValidationError("نوع یادآوری نامعتبر است")


def snooze_next_run(current: datetime, amount_text: str) -> datetime:
    """Push a one-time reminder forward by a duration like ``30m``/``2h``."""
    seconds = parse_duration(amount_text)
    return current + timedelta(seconds=seconds)


def schedule_display(schedule: str, reminder_type: str) -> str:
    """Human-readable schedule for listing reminders."""
    if reminder_type == "one_time":
        return schedule
    if reminder_type == "daily":
        return f"روزانه {schedule}"
    if reminder_type == "weekly":
        day_token, time_part = schedule.split(maxsplit=1)
        return f"هفتگی {day_token} {time_part}"
    day_token, time_part = schedule.split(maxsplit=1)
    return f"ماهانه روز {day_token} ساعت {time_part}"


def format_utc_for_tz(value: datetime | None, tz_name: str) -> str:
    """Format a naive UTC datetime in the given timezone."""
    if value is None:
        return "—"
    tz = get_timezone(tz_name)
    aware = value.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    return aware.strftime("%Y-%m-%d %H:%M")


def _split_time_text(args: str) -> tuple[str, str]:
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        raise ValidationError("متن یادآوری را وارد کنید")
    return parts[0].strip(), parts[1].strip()


def _parse_hhmm(value: str) -> tuple[int, int]:
    if not re.fullmatch(r"\d{1,2}:\d{2}", value):
        raise ValidationError("زمان باید به شکل HH:MM باشد")
    hour, minute = (int(x) for x in value.split(":"))
    if hour > 23 or minute > 59:
        raise ValidationError("زمان خارج از محدوده است")
    return hour, minute


def _next_daily(hour: int, minute: int, tz_name: str | None) -> datetime:
    tz = get_timezone(tz_name)
    candidate = datetime.now(tz=tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= datetime.now(tz=tz):
        candidate += timedelta(days=1)
    return candidate.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def _next_weekly(weekday: int, hour: int, minute: int, tz_name: str | None) -> datetime:
    tz = get_timezone(tz_name)
    candidate = datetime.now(tz=tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
    while candidate.weekday() != weekday:
        candidate += timedelta(days=1)
    if candidate <= datetime.now(tz=tz):
        candidate += timedelta(days=7)
    return candidate.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def _next_monthly(day_of_month: int, hour: int, minute: int, tz_name: str | None) -> datetime:
    tz = get_timezone(tz_name)
    candidate = datetime.now(tz=tz).replace(second=0, microsecond=0)
    while True:
        candidate = candidate.replace(hour=hour, minute=minute)
        if candidate.day == day_of_month and candidate > datetime.now(tz=tz):
            break
        candidate += timedelta(days=1)
    return candidate.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
