"""Calculator safety and correctness tests."""

from __future__ import annotations

import math

import pytest

from selfbot.services.calculator import CalculationError, Calculator


@pytest.fixture
def calc() -> Calculator:
    return Calculator()


ATTACKS = [
    "__import__('os')",
    "__import__('os').system('whoami')",
    "().__class__.__bases__[0].__subclasses__()",
    "'abc'",
    '"abc"',
    "open('/etc/passwd').read()",
    "print(1)",
    "_",
    "[]",
    "{}",
    "(1).__class__",
    "a",
    "1 + _",
    "lambda: 1",
    "[x for x in range(10)]",
    "import os",
    "eval('1')",
    "exec('x=1')",
    "1 if True else 0",
    "True",
    "None",
]


def test_simple_arithmetic(calc: Calculator) -> None:
    assert calc.evaluate("2 + 3") == 5
    assert calc.evaluate("10 * 4 - 3") == 37
    assert calc.evaluate("2 ** 10") == 1024
    assert calc.evaluate("(1 + 2) * 3") == 9
    assert calc.evaluate("-5 + 10") == 5


def test_float_results(calc: Calculator) -> None:
    assert calc.evaluate("7 / 2") == 3.5
    assert abs(calc.evaluate("sqrt(2)") - math.sqrt(2)) < 1e-9


def test_math_functions(calc: Calculator) -> None:
    assert calc.evaluate("sin(0)") == pytest.approx(0.0)
    assert calc.evaluate("cos(0)") == pytest.approx(1.0)
    assert calc.evaluate("sqrt(144)") == pytest.approx(12.0)
    assert calc.evaluate("log(e)") == pytest.approx(1.0)
    assert calc.evaluate("abs(-42)") == 42
    assert calc.evaluate("round(3.14159)") == 3
    assert calc.evaluate("pow(2, 10)") == 1024
    assert calc.evaluate("factorial(5)") == 120


def test_constants(calc: Calculator) -> None:
    assert calc.evaluate("pi") == pytest.approx(math.pi)
    assert calc.evaluate("e") == pytest.approx(math.e)
    assert calc.evaluate("2 * pi") == pytest.approx(2 * math.pi)


@pytest.mark.parametrize("expression", ATTACKS)
def test_unsafe_expressions_are_rejected(calc: Calculator, expression: str) -> None:
    with pytest.raises(CalculationError):
        calc.evaluate(expression)


def test_unknown_symbols(calc: Calculator) -> None:
    with pytest.raises(CalculationError):
        calc.evaluate("foo(1)")
    with pytest.raises(CalculationError):
        calc.evaluate("2 + undefined_variable")


def test_keyword_args_rejected(calc: Calculator) -> None:
    with pytest.raises(CalculationError):
        calc.evaluate("pow(base=2, exp=3)")
