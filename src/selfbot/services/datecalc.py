"""Date arithmetic: add/subtract days, weeks, months, years."""

from __future__ import annotations

import re
from datetime import date, timedelta

from selfbot.utils.validators import ValidationError

_PATTERN = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)\s*([dwmy])\s*$",
    re.IGNORECASE,
)


class DateCalculator:
    """Calculates a target date from an expression like ``2026-10-01 + 30d``."""

    UNITS = {"d": "روز", "w": "هفته", "m": "ماه", "y": "سال"}

    @classmethod
    def calculate(cls, expression: str) -> str:
        match = _PATTERN.match(expression)
        if not match:
            raise ValidationError("قالب معتبر نیست")

        start_text, sign, amount_text, unit = match.groups()
        try:
            start = date.fromisoformat(start_text)
            amount = int(amount_text)
        except ValueError:
            raise ValidationError("تاریخ معتبر نیست") from None

        offset = timedelta(days=_amount_in_days(amount, unit.lower()))
        result = start + offset if sign == "+" else start - offset

        label = cls.UNITS[unit.lower()]
        sign_label = "بعد از" if sign == "+" else "قبل از"
        return (
            f"📅 {msg_bold(result.isoformat())}\n"
            f"{amount} {label} {sign_label} {start_text}"
        )


def _amount_in_days(amount: int, unit: str) -> int:
    if unit == "d":
        return amount
    if unit == "w":
        return amount * 7
    if unit == "m":
        return amount * 30
    if unit == "y":
        return amount * 365
    raise ValidationError("واحد ناشناخته")


def msg_bold(text: str) -> str:
    """Wrap text in markdown bold for Telegram messages."""
    return f"**{text}**"
