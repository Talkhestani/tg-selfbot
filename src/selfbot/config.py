"""Application configuration through environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    api_id: int | None = Field(default=None, description="Telegram API ID")
    api_hash: str = Field(default="", description="Telegram API hash")
    session_name: str = "selfbot"
    session_string: str = ""

    # Owner / permissions
    owner_id: int | None = Field(default=None, description="Owner Telegram user ID")

    # AI integration (empty = disabled)
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_api_base: str = ""
    ai_enabled: bool = False
    ai_daily_limit: int = 50
    ai_context_length: int = 10
    ai_max_tokens: int = 300
    ai_temperature: float = 0.7

    # Database
    database_url: str = "sqlite+aiosqlite:///data/app.db"

    # Timezone
    timezone: str = "Asia/Tehran"

    # Downloader
    download_dir: str = "downloads"
    max_download_size_mb: int = 500
    download_timeout: int = 300

    # External keys
    weather_api_key: str = ""
    url_shortener_api_key: str = ""

    # Logging
    log_level: str = "INFO"

    # Commands
    command_prefix: str = "@"

    # Deletion confirmation
    require_confirmation: bool = True

    # Profile automation intervals (seconds)
    profile_update_interval: int = 60
    bio_clock_interval: int = 300

    @field_validator("owner_id", mode="before")
    @classmethod
    def empty_owner(cls, v):
        if v == "" or v is None:
            return None
        return int(v)

    @field_validator("api_id")
    @classmethod
    def validate_api_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("api_id باید یک عدد مثبت باشد")
        return value

    @field_validator("max_download_size_mb")
    @classmethod
    def validate_max_download_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_download_size_mb باید بزرگ‌تر از صفر باشد")
        return value

    @property
    def data_dir(self) -> Path:
        """Directory holding application data files."""
        base = self.database_url.split("///")[-1]
        if base == "app.db":
            return Path.cwd() / "data"
        path = Path(base).parent
        return path if str(path) else Path.cwd() / "data"

    @property
    def download_path(self) -> Path:
        """Absolute path of the download directory."""
        return Path(self.download_dir).resolve()

    @property
    def ai_configured(self) -> bool:
        """Whether an AI provider is fully configured."""
        return bool(self.ai_provider and self.ai_api_key and self.ai_model)

    def secret_summary(self) -> tuple[str, str, str, str]:
        """Non-sensitive configuration summary for logs."""
        return (
            "api_id=<set>" if self.api_id else "api_id=<missing>",
            f"session={self.session_name!r}",
            f"timezone={self.timezone!r}",
            "ai=configured" if self.ai_configured else "ai=disabled",
        )

    message_backup_enabled: bool = False
    message_backup_remove_on_seen: bool = True
    proxy_enabled: bool = True

    def __str__(self) -> str:
        return ", ".join(self.secret_summary())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def load_dotenv_safe() -> None:
    """Load .env without overriding already-set environment variables."""
    from dotenv import load_dotenv

    load_dotenv(verbose=False, override=False)
