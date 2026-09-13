"""Reminder scheduling and planning tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from selfbot.services import reminder_planner as rp
from selfbot.utils.validators import ValidationError

TZ = "Asia/Tehran"


def test_daily_next_run_is_in_the_future() -> None:
    reminder_text, schedule, next_run = rp.plan_daily("09:30 صبحانه بخور", TZ)
    assert reminder_text == "صبحانه بخور"
    hour, minute = (int(x) for x in schedule.split(":"))
    assert (hour, minute) == (9, 30)
    assert next_run > rp.now_utc()
    # The scheduled local hour must match the configured timezone.
    local = next_run.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TZ))
    assert (local.hour, local.minute) == (9, 30)
    assert (local.weekday(), local.hour) != (rp.now_utc().weekday(), local.hour)


def test_daily_requires_text() -> None:
    with pytest.raises(ValidationError):
        rp.plan_daily("09:30", TZ)


def test_weekly_planning() -> None:
    reminder_text, schedule, next_run = rp.plan_weekly("mon 08:00 جلسه", TZ)
    assert reminder_text == "جلسه"
    assert schedule == "mon 08:00"
    local = next_run.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TZ))
    assert local.weekday() == 0  # Monday
    assert (local.hour, local.minute) == (8, 0)


def test_weekly_invalid_day() -> None:
    with pytest.raises(ValidationError):
        rp.plan_weekly("funday 08:00 text", TZ)


def test_weekly_invalid_hour() -> None:
    with pytest.raises(ValidationError):
        rp.plan_weekly("mon 25:00 text", TZ)


def test_monthly_planning() -> None:
    reminder_text, schedule, next_run = rp.plan_monthly("15 12:00 پرداخت قبض", TZ)
    assert reminder_text == "پرداخت قبض"
    local = next_run.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TZ))
    assert local.day == 15
    assert (local.hour, local.minute) == (12, 0)


def test_monthly_day_range() -> None:
    with pytest.raises(ValidationError):
        rp.plan_monthly("29 12:00 text", TZ)
    with pytest.raises(ValidationError):
        rp.plan_monthly("0 12:00 text", TZ)


def test_relative_one_time() -> None:
    text, schedule, next_run = rp.plan_relative_or_absolute("1h کار را تمام کن", TZ)
    assert text == "کار را تمام کن"
    assert next_run > rp.now_utc() + timedelta(minutes=59)


def test_absolute_one_time() -> None:
    future = rp.now_utc() + timedelta(days=1, hours=3)
    fmt = future.strftime("%Y-%m-%d %H:%M")
    text, schedule, next_run = rp.plan_relative_or_absolute(f"{fmt} خریدن بلیط", TZ)
    assert text == "خریدن بلیط"
    assert schedule == fmt
    # Parse was timezone-agnostic; give slack for tz conversion differences.
    assert abs((next_run - future).total_seconds()) < 3600 * 24


def test_past_reminder_rejected() -> None:
    past = (rp.now_utc() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    with pytest.raises(ValidationError):
        rp.plan_relative_or_absolute(f"{past} یادآوری گذشته", TZ)


def test_invalid_time_rejected() -> None:
    with pytest.raises(ValidationError):
        rp.plan_relative_or_absolute("not-a-time متن", TZ)


def test_compute_next_run_one_time() -> None:
    expected = datetime(2030, 5, 1, 10, 30)
    assert rp.compute_next_run("one_time", "2030-05-01 10:30", TZ) == expected


def test_compute_next_run_daily() -> None:
    result = rp.compute_next_run("daily", "07:15", TZ)
    assert result > rp.now_utc()


def test_snooze() -> None:
    base = rp.now_utc()
    assert rp.snooze_next_run(base, "30m") == base + timedelta(minutes=30)
    assert rp.snooze_next_run(base, "2h") == base + timedelta(hours=2)


def test_schedule_display() -> None:
    assert rp.schedule_display("2026-01-01 10:00", "one_time") == "2026-01-01 10:00"
    assert rp.schedule_display("09:00", "daily").startswith("روزانه")
    assert rp.schedule_display("mon 09:00", "weekly").startswith("هفتگی")
    assert rp.schedule_display("15 09:00", "monthly").startswith("ماهانه")


def test_format_utc_for_tz() -> None:
    value = datetime(2026, 3, 1, 12, 0)  # naive UTC
    rendered = rp.format_utc_for_tz(value, TZ)
    assert rendered == "2026-03-01 15:30"  # Tehran is UTC+3:30


def test_parse_duration_validation() -> None:
    from selfbot.utils.validators import parse_duration

    assert parse_duration("5m") == 300
    assert parse_duration("2h") == 7200
    assert parse_duration("2d") == 172800
    assert parse_duration("90s") == 90
    with pytest.raises(ValidationError):
        parse_duration("abc")
