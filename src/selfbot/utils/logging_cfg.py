"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys

from selfbot.config import Settings


class RedactingFilter(logging.Filter):
    """Prevent sensitive values from ever reaching logs."""

    _SENSITIVE = (
        "api_hash",
        "api_key",
        "session_string",
        "password",
        "secret",
        "token",
        "jwt",
        "authorization",
        "ai_api_key",
        "url_shortener_api_key",
        "weather_api_key",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        lowered = message.lower()
        for keyword in self._SENSITIVE:
            if keyword in lowered:
                record.msg = "<redacted>"
                record.args = None
                break
        return True


def setup_logging(settings: Settings) -> None:
    """Configure root logger with a helpful console handler."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)
    root.propagate = False

    # Keep noisy libraries quieter by default.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
