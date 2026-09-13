"""Unit, temperature, time, and data-size conversion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


class ConversionError(Exception):
    """Raised when a conversion is not possible."""


@dataclass(frozen=True)
class UnitDef:
    name: str
    aliases: tuple[str, ...]
    to_base: Callable[[float], float]
    from_base: Callable[[float], float]


def _linear(factor: float) -> tuple[Callable[[float], float], Callable[[float], float]]:
    return (lambda v: v * factor, lambda v: v / factor)


_LENGTH: dict[str, UnitDef] = {}
_WEIGHT: dict[str, UnitDef] = {}
_TIME: dict[str, UnitDef] = {}
_DATA: dict[str, UnitDef] = {}


def _fill_definitions() -> None:
    global _LENGTH, _WEIGHT, _TIME, _DATA
    length_factors = {
        "m": (1.0, ("meter", "meters", "mtr", "m")),
        "km": (1000.0, ("kilometer", "kilometers", "kilometre")),
        "cm": (0.01, ("centimeter", "centimeters")),
        "mm": (0.001, ("millimeter", "millimeters")),
        "mile": (1609.344, ("miles", "mi")),
        "yard": (0.9144, ("yards", "yd")),
        "foot": (0.3048, ("feet", "ft")),
        "inch": (0.0254, ("inches", "in")),
        "nauticalmile": (1852.0, ("nautical miles", "nmi")),
    }
    for unit, (factor, aliases) in length_factors.items():
        to_base, from_base = _linear(factor)
        _LENGTH[unit] = UnitDef(unit, aliases, to_base, from_base)

    weight_factors = {
        "kg": (1.0, ("kilogram", "kilograms", "kilo")),
        "g": (0.001, ("gram", "grams")),
        "mg": (1e-6, ("milligram", "milligrams")),
        "ton": (1000.0, ("tonne", "tonnes", "metric ton")),
        "lb": (0.45359237, ("lbs", "pound", "pounds")),
        "oz": (0.0283495231, ("ounce", "ounces")),
    }
    for unit, (factor, aliases) in weight_factors.items():
        to_base, from_base = _linear(factor)
        _WEIGHT[unit] = UnitDef(unit, aliases, to_base, from_base)

    time_factors = {
        "s": (1.0, ("sec", "second", "seconds")),
        "min": (60.0, ("minute", "minutes", "mins")),
        "h": (3600.0, ("hr", "hour", "hours")),
        "day": (86400.0, ("days",)),
        "week": (604800.0, ("weeks",)),
        "month": (2629800.0, ("months",)),
        "year": (31557600.0, ("years",)),
    }
    for unit, (factor, aliases) in time_factors.items():
        to_base, from_base = _linear(factor)
        _TIME[unit] = UnitDef(unit, aliases, to_base, from_base)

    data_factors = {
        "b": (1.0, ("byte", "bytes")),
        "kb": (1024.0, ("kilobyte", "kilobytes")),
        "mb": (1024**2, ("megabyte", "megabytes")),
        "gb": (1024**3, ("gigabyte", "gigabytes")),
        "tb": (1024**4, ("terabyte", "terabytes")),
        "bit": (0.125, ("bits",)),
    }
    for unit, (factor, aliases) in data_factors.items():
        to_base, from_base = _linear(factor)
        _DATA[unit] = UnitDef(unit, aliases, to_base, from_base)


_fill_definitions()

# Temperature handled separately (affine conversion).
_TEMP_UNITS = ("c", "f", "k", "kelvin")


def _celsius_to_base(c: float) -> float:
    return c + 273.15


def _base_to_celsius(k: float) -> float:
    return k - 273.15


_CATEGORIES: dict[str, dict[str, UnitDef]] = {
    "length": _LENGTH,
    "weight": _WEIGHT,
    "time": _TIME,
    "data": _DATA,
}


class UnitConverter:
    """Converts values between units of supported categories."""

    CATEGORY_LABELS = {
        "length": "طول",
        "weight": "وزن",
        "temperature": "دما",
        "time": "زمان",
        "data": "حجم داده",
    }

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        category, source = self._find_unit(from_unit)
        _, target = self._find_unit(to_unit)
        if source is target and category != "temperature":
            raise ConversionError("واحد مبدأ و مقصد یکسان است")
        if category == "temperature":
            return self._convert_temperature(value, from_unit.lower(), to_unit.lower())
        base = source.to_base(value)
        return target.from_base(base)

    def _convert_temperature(self, value: float, source: str, target: str) -> float:
        from_unit = self._canonical_temp(source)
        to_unit = self._canonical_temp(target)
        if from_unit == to_unit:
            raise ConversionError("واحد مبدأ و مقصد یکسان است")
        # Normalise to Celsius.
        if from_unit == "f":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "k":
            celsius = value - 273.15
        else:
            celsius = value
        if to_unit == "f":
            return celsius * 9 / 5 + 32
        if to_unit == "k":
            return celsius + 273.15
        return celsius

    @staticmethod
    def _canonical_temp(unit: str) -> str:
        if unit in ("c", "celsius", "centigrade"):
            return "c"
        if unit in ("f", "fahrenheit"):
            return "f"
        if unit in ("k", "kelvin"):
            return "k"
        raise ConversionError("واحد دما پشتیبانی نمی‌شود")

    def _find_unit(self, text: str) -> tuple[str, UnitDef]:
        lowered = text.strip().lower().replace(" ", "")
        for category, table in _CATEGORIES.items():
            for unit, definition in table.items():
                if unit == lowered or lowered in definition.aliases:
                    return category, definition
        try:
            canonical = self._canonical_temp(lowered)
            temp_table = {
                "c": UnitDef("c", ("celsius", "centigrade"), _celsius_to_base, _base_to_celsius),
                "f": UnitDef("f", ("fahrenheit",), _celsius_to_base, _base_to_celsius),
                "k": UnitDef("k", ("kelvin",), _celsius_to_base, _base_to_celsius),
            }
            return "temperature", temp_table[canonical]
        except ConversionError as exc:
            raise ConversionError("واحد پشتیبانی نمی‌شود") from exc

    def find_category(self, unit: str) -> str | None:
        try:
            category, _ = self._find_unit(unit)
            return category
        except ConversionError:
            return None
