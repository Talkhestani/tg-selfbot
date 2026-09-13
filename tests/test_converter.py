"""Unit converter tests."""

from __future__ import annotations

import pytest

from selfbot.services.converter import ConversionError, UnitConverter


@pytest.fixture
def converter() -> UnitConverter:
    return UnitConverter()


@pytest.mark.parametrize(
    ("value", "source", "target", "expected"),
    [
        (1.0, "km", "m", 1000.0),
        (100.0, "cm", "m", 1.0),
        (1.0, "mile", "km", 1.609344),
        (1.0, "kg", "g", 1000.0),
        (1.0, "lb", "oz", 16.0),
        (1.0, "h", "min", 60.0),
        (1.0, "day", "h", 24.0),
        (1.0, "gb", "mb", 1024.0),
        (1.0, "tb", "gb", 1024.0),
    ],
)
def test_linear_conversions(converter, value, source, target, expected) -> None:
    assert converter.convert(value, source, target) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "source", "target", "expected"),
    [
        (0.0, "c", "f", 32.0),
        (100.0, "c", "k", 373.15),
        (32.0, "f", "c", 0.0),
        (98.6, "f", "k", pytest.approx(310.15)),
        (300.0, "k", "c", 26.85),
        (300.0, "k", "f", pytest.approx(80.33)),
    ],
)
def test_temperature_conversions(converter, value, source, target, expected) -> None:
    assert converter.convert(value, source, target) == pytest.approx(expected)


def test_aliases_are_accepted(converter) -> None:
    assert converter.convert(1, "kilometers", "m") == pytest.approx(1000)
    assert converter.convert(1, "meters", "feet") == pytest.approx(1 / 0.3048)
    assert converter.convert(1, "lbs", "ounces") == pytest.approx(16)


def test_same_unit_rejected(converter) -> None:
    with pytest.raises(ConversionError):
        converter.convert(5, "km", "kilometers")


def test_unknown_unit_rejected(converter) -> None:
    with pytest.raises(ConversionError):
        converter.convert(5, "parsec", "m")


def test_find_category(converter) -> None:
    assert converter.find_category("mile") == "length"
    assert converter.find_category("lb") == "weight"
    assert converter.find_category("kelvin") == "temperature"
    assert converter.find_category("nonsense") is None
