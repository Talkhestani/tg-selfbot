"""Generic transformation tools: JSON, encoding, hashing and more.

These are pure functions with no I/O so they are easy to test and reuse.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import html as html_module
import json
import random
import re
import uuid as uuid_module
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, unquote_plus

import jwt as pyjwt
from markdown import markdown as md_to_html

from selfbot.quotes import QUOTES
from selfbot.swears import SWEARS


def random_quote() -> tuple[str, str] | None:
    """Return a random (text, author) quote."""
    if not QUOTES:
        return None
    entry = random.choice(QUOTES)
    return str(entry.get("text", "")), str(entry.get("author", ""))


def random_swears(count: int) -> list[str]:
    """Return up to `count` random insult texts."""
    if count <= 0 or not SWEARS:
        return []
    return random.sample(SWEARS, min(count, len(SWEARS)))


class ToolError(Exception):
    """Raised when a tool cannot process its input."""


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def format_json(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolError(_json_error_message(exc, text)) from exc
    return json.dumps(data, ensure_ascii=False, indent=2)


def minify_json(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolError(_json_error_message(exc, text)) from exc
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def validate_json(text: str) -> tuple[bool, str | None]:
    try:
        json.loads(text)
        return True, None
    except json.JSONDecodeError as exc:
        return False, _json_error_message(exc, text)


def _json_error_message(exc: json.JSONDecodeError, text: str) -> str:
    position = exc.pos
    line = text.count("\n", 0, position) + 1
    column = position - (text.rfind("\n", 0, position) + 1) + 1
    return f"خطای سینتکس در خط {line}، ستون {column}: {exc.msg}"


# ---------------------------------------------------------------------------
# Base64
# ---------------------------------------------------------------------------
def b64_encode(text: str) -> str:
    try:
        data = text.encode("utf-8")
    except UnicodeError as exc:
        raise ToolError("متن قابل کدگذاری نیست") from exc
    return base64.b64encode(data).decode("ascii")


def b64_decode(text: str) -> str:
    try:
        # Strip whitespace/newlines which are commonly added by messengers.
        cleaned = "".join(text.split())
        data = base64.b64decode(cleaned, validate=True)
        return data.decode("utf-8")
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise ToolError("متن ورودی Base64 معتبر نیست") from exc


# ---------------------------------------------------------------------------
# URL encoding
# ---------------------------------------------------------------------------
def url_encode(text: str) -> str:
    return quote(text, safe="")


def url_decode(text: str) -> str:
    return unquote_plus(text)


# ---------------------------------------------------------------------------
# UUID
# ---------------------------------------------------------------------------
def generate_uuids(count: int = 1) -> list[str]:
    return [str(uuid_module.uuid4()) for _ in range(max(1, count))]


# ---------------------------------------------------------------------------
# Hash
# ---------------------------------------------------------------------------
_HASH_ALGORITHMS = ("md5", "sha1", "sha256", "sha512")


def hash_text(algorithm: str, text: str) -> str:
    algorithm = algorithm.lower()
    if algorithm not in _HASH_ALGORITHMS:
        raise ToolError(f"unsupported algorithm: {algorithm}")
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def supported_hashes() -> tuple[str, ...]:
    return _HASH_ALGORITHMS


# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------
def regex_match(pattern: str, text: str) -> tuple[int, list[dict[str, Any]]]:
    """Return (number_of_matches, list of match details)."""
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ToolError(f"الگوی نامعتبر: {exc}") from exc

    matches: list[dict[str, Any]] = []
    for match in compiled.finditer(text):
        details = {
            "match": match.group(0),
            "start": match.start(),
            "end": match.end(),
            "groups": list(match.groups()),
        }
        matches.append(details)
    return len(matches), matches


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------
def now_unix() -> int:
    return int(datetime.now(UTC).timestamp())


def datetime_to_unix(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp())


def unix_to_datetime(unix: int) -> datetime:
    return datetime.fromtimestamp(unix, tz=UTC)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def decode_jwt(token: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Decode and return (header, payload) of a JWT.

    Signature verification is intentionally not performed.
    """
    try:
        header = pyjwt.get_unverified_header(token)
        payload = pyjwt.decode(token, options={"verify_signature": False})
    except pyjwt.PyJWTError as exc:
        raise ToolError("توکن JWT نامعتبر است") from exc
    return header, payload


# ---------------------------------------------------------------------------
# Color conversion (HEX / RGB / HSL)
# ---------------------------------------------------------------------------
def parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ToolError("کد HEX باید ۶ رقم باشد")
    try:
        r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise ToolError("کد HEX معتبر نیست") from exc
    validate_rgb(r, g, b)
    return r, g, b


def parse_rgb(value: str) -> tuple[int, int, int]:
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    if len(parts) != 3:
        raise ToolError("قالب RGB باید سه مقدار باشد")
    try:
        r, g, b = (int(p) for p in parts)
    except ValueError as exc:
        raise ToolError("مقادیر RGB باید عدد باشند") from exc
    validate_rgb(r, g, b)
    return r, g, b


def validate_rgb(r: int, g: int, b: int) -> None:
    if not all(0 <= channel <= 255 for channel in (r, g, b)):
        raise ToolError("مقادیر RGB باید بین ۰ تا ۲۵۵ باشند")


def rgb_to_hex(r: int, g: int, b: int) -> str:
    validate_rgb(r, g, b)
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    validate_rgb(r, g, b)
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    max_c, min_c = max(rn, gn, bn), min(rn, gn, bn)
    lightness = (max_c + min_c) / 2.0
    delta = max_c - min_c
    if delta == 0:
        hue, saturation = 0.0, 0.0
    else:
        saturation = delta / (1 - abs(2 * lightness - 1)) if lightness not in (0.0, 1.0) else 0.0
        if max_c == rn:
            hue = 60.0 * (((gn - bn) / delta) % 6)
        elif max_c == gn:
            hue = 60.0 * (((bn - rn) / delta) + 2)
        else:
            hue = 60.0 * (((rn - gn) / delta) + 4)
    return round(hue, 1), round(saturation * 100, 1), round(lightness * 100, 1)


def describe_color(color_input: str) -> dict[str, str]:
    stripped = color_input.strip().lstrip("#")
    if "," in stripped:
        r, g, b = parse_rgb(stripped)
    elif re.fullmatch(r"[0-9a-fA-F]{3,6}", stripped):
        r, g, b = parse_hex_color(stripped)
    else:
        raise ToolError("فرمت رنگ پشتیبانی نمی‌شود")
    hue, sat, light = rgb_to_hsl(r, g, b)
    return {
        "hex": rgb_to_hex(r, g, b),
        "rgb": f"rgb({r}, {g}, {b})",
        "hsl": f"hsl({hue}, {sat}%, {light}%)",
    }


# ---------------------------------------------------------------------------
# Markdown <-> HTML
# ---------------------------------------------------------------------------
def markdown_to_html(text: str) -> str:
    return md_to_html(text, extensions=["extra", "sane_lists"])


def html_to_markdown(text: str) -> str:
    """Best-effort HTML -> Markdown conversion for common tags."""
    imports_html = html_module
    result: str = text
    replacements = {
        "<strong>": "**", "</strong>": "**",
        "<b>": "**", "</b>": "**",
        "<em>": "_", "</em>": "_",
        "<i>": "_", "</i>": "_",
        "<h1>": "# ", "</h1>": "\n",
        "<h2>": "## ", "</h2>": "\n",
        "<h3>": "### ", "</h3>": "\n",
        "<h4>": "#### ", "</h4>": "\n",
        "<ul>": "", "</ul>": "\n",
        "<ol>": "", "</ol>": "\n",
        "<li>": "- ", "</li>": "\n",
        "<blockquote>": "> ", "</blockquote>": "\n",
        "<code>": "`", "</code>": "`",
        "<hr>": "---\n", "<hr/>": "---\n",
    }
    for tag, replacement in replacements.items():
        result = result.replace(tag, replacement)
    result = re.sub(r"<br\s*/?>", "\n", result)
    result = re.sub(r"<!--.*?-->", "", result, flags=re.DOTALL)
    result = imports_html.unescape(result)
    return result.strip()


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
def strip_newlines(text: str, limit: int) -> str:
    """Return the first ``limit`` lines of a text."""
    return "\n".join(text.splitlines()[:limit])
