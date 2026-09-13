"""Toolbox (JSON / base64 / hash / regex / timestamps / color / markdown) tests."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

import pytest

from selfbot.services import toolbox
from selfbot.services.toolbox import ToolError


# -- JSON -----------------------------------------------------------------
def test_format_json() -> None:
    output = toolbox.format_json('{"a":1,"b":[1,2]}')
    assert json.loads(output) == {"a": 1, "b": [1, 2]}
    assert "\n" in output


def test_format_json_invalid() -> None:
    with pytest.raises(ToolError):
        toolbox.format_json("{invalid")
    with pytest.raises(ToolError):
        toolbox.minify_json("{invalid")


def test_minify_json() -> None:
    assert toolbox.minify_json('{"a": 1, "b": ["x", "y"]}') == '{"a":1,"b":["x","y"]}'


def test_validate_json() -> None:
    ok, error = toolbox.validate_json('{"a":1}')
    assert ok is True and error is None
    ok, error = toolbox.validate_json("{nope")
    assert ok is False and error is not None


# -- base64 ---------------------------------------------------------------
def test_b64_roundtrip() -> None:
    message = "سلام دنیا"
    encoded = toolbox.b64_encode(message)
    assert toolbox.b64_decode(encoded) == message


def test_b64_decode_ignores_whitespace() -> None:
    assert toolbox.b64_decode("aGVsbG8=\n") == "hello"
    assert toolbox.b64_decode(" a G V s b G 8 = ") == "hello"


def test_b64_decode_invalid() -> None:
    with pytest.raises(ToolError):
        toolbox.b64_decode("!!! not base64 !!!")


# -- URL encoding ---------------------------------------------------------
def test_url_roundtrip() -> None:
    text = "hello world/متن"
    assert toolbox.url_decode(toolbox.url_encode(text)) == text


# -- UUID ----------------------------------------------------------------
def test_uuid_generation() -> None:
    uuids = toolbox.generate_uuids(3)
    assert len(uuids) == 3
    assert len(set(uuids)) == 3
    for value in uuids:
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value)


# -- hash ---------------------------------------------------------------
def test_hash_text_known_values() -> None:
    assert toolbox.hash_text("md5", "hello") == "5d41402abc4b2a76b9719d911017c592"
    assert toolbox.hash_text("sha256", "hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_hash_invalid_algorithm() -> None:
    with pytest.raises(ToolError):
        toolbox.hash_text("blake42", "x")


# -- regex ---------------------------------------------------------------
def test_regex_match() -> None:
    count, matches = toolbox.regex_match(r"\d+", "a1 b22 c333")
    assert count == 3
    assert matches[0]["match"] == "1"
    assert matches[2]["groups"] == []


def test_regex_with_groups() -> None:
    count, matches = toolbox.regex_match(r"(\w+)-(\d+)", "item-42")
    assert count == 1
    assert matches[0]["groups"] == ["item", "42"]


def test_regex_invalid_pattern() -> None:
    with pytest.raises(ToolError):
        toolbox.regex_match("(", "text")


# -- timestamps ------------------------------------------------------------
def test_now_unix() -> None:
    unix = toolbox.now_unix()
    assert abs(unix - int(datetime.now(UTC).timestamp())) < 5


def test_unix_roundtrip() -> None:
    now = datetime.now(UTC).replace(second=0, microsecond=0, tzinfo=None)
    assert toolbox.unix_to_datetime(toolbox.datetime_to_unix(now)).replace(tzinfo=None) == now


# -- JWT -------------------------------------------------------------------
def test_decode_jwt_unverified() -> None:
    import jwt as pyjwt

    token = pyjwt.encode(
        {"sub": "123", "name": "tester"},
        "x" * 32,
        algorithm="HS256",
    )
    header, payload = toolbox.decode_jwt(token)
    assert header["alg"] == "HS256"
    assert payload["sub"] == "123"


def test_decode_jwt_invalid() -> None:
    with pytest.raises(ToolError):
        toolbox.decode_jwt("not-a-jwt")


# -- color -----------------------------------------------------------------
def test_hex_to_rgb() -> None:
    assert toolbox.parse_hex_color("#FF0000") == (255, 0, 0)
    assert toolbox.parse_hex_color("0f0") == (0, 255, 0)


def test_rgb_to_hex() -> None:
    assert toolbox.rgb_to_hex(255, 0, 0) == "#FF0000"


def test_color_description() -> None:
    details = toolbox.describe_color("#ff0000")
    assert details["hex"] == "#FF0000"
    assert details["rgb"] == "rgb(255, 0, 0)"
    assert details["hsl"].startswith("hsl(0.0")


def test_parse_rgb() -> None:
    assert toolbox.parse_rgb("10, 20, 30") == (10, 20, 30)


def test_invalid_color() -> None:
    with pytest.raises(ToolError):
        toolbox.describe_color("#GGGGGG")
    with pytest.raises(ToolError):
        toolbox.parse_hex_color("#12345")
    with pytest.raises(ToolError):
        toolbox.parse_rgb("300, 0, 0")


# -- markup ----------------------------------------------------------------
def test_markdown_to_html() -> None:
    html = toolbox.markdown_to_html("**bold** and *italic*")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_html_to_markdown() -> None:
    md = toolbox.html_to_markdown("<b>important</b> &amp; <code>x</code>")
    assert md == "**important** & `x`"
