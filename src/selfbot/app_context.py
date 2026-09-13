"""Global application state.

A thin registry that wires services together at startup. Kept minimal: it
stores the database and settings so background tasks and services can access
them without long dependency chains. Tests can call :func:`reset` to clear it.
"""

from __future__ import annotations

from typing import Any

from selfbot.config import Settings

_database: Any = None
_settings: Settings | None = None


def init(database: Any, settings: Settings) -> None:
    """Register the database and settings as the global application state."""
    global _database, _settings
    _database = database
    _settings = settings


def reset() -> None:
    """Clear the global application state (used by tests)."""
    global _database, _settings
    _database = None
    _settings = None


def get_database() -> Any:
    if _database is None:
        raise RuntimeError("application database is not initialised")
    return _database


def get_settings() -> Settings:
    if _settings is None:
        raise RuntimeError("application settings are not initialised")
    return _settings
