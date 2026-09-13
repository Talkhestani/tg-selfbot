"""Safe arithmetic expression evaluator based on Python's AST.

Supports arithmetic operators, parentheses, powers, modulo, division and a
whitelist of math functions. Never uses ``eval`` / ``exec``.
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable
from typing import Any

_ALLOWED_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_MATH_FUNCTIONS: dict[str, Callable[..., int | float]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "pow": math.pow,
}

_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

_FUNCTION_NAMES = set(_MATH_FUNCTIONS)


class CalculationError(Exception):
    """Raised for any unsafe or invalid expression."""


class Calculator:
    """Evaluates simple math expressions safely."""

    def evaluate(self, expression: str) -> float | int:
        if not isinstance(expression, str) or not expression.strip():
            raise CalculationError("empty expression")

        node = self._parse(expression)
        try:
            result = self._eval(node)
        except (ZeroDivisionError, ValueError, OverflowError, TypeError) as exc:
            raise CalculationError(str(exc)) from exc

        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result

    @staticmethod
    def _parse(expression: str) -> ast.AST:
        try:
            return ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise CalculationError(f"invalid expression: {exc.msg}") from exc

    def _eval(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        if isinstance(node, ast.BinOp):
            op = _ALLOWED_BIN_OPS.get(type(node.op))
            if op is None:
                raise CalculationError("operator not allowed")
            left = self._eval(node.left)
            right = self._eval(node.right)
            return op(left, right)
        if isinstance(node, ast.UnaryOp):
            op = _ALLOWED_UNARY_OPS.get(type(node.op))
            if op is None:
                raise CalculationError("operator not allowed")
            return op(self._eval(node.operand))
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise CalculationError("literal not allowed")
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.Name):
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            raise CalculationError(f"unknown name: {node.id}")
        raise CalculationError(f"unsupported syntax: {type(node).__name__}")

    def _eval_call(self, node: ast.Call) -> float | int:
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name not in _FUNCTION_NAMES:
            raise CalculationError("unknown function")
        if node.keywords:
            raise CalculationError("keyword arguments not allowed")
        args = [self._eval(arg) for arg in node.args]
        try:
            return _MATH_FUNCTIONS[name](*args)
        except (TypeError, ValueError, OverflowError) as exc:
            raise CalculationError(f"{name}({', '.join(map(str, args))}) failed") from exc
