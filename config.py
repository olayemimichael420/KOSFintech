"""
KOSFintech configuration layer.

All environment-dependent configuration is centralized here.
Business logic must not read environment variables directly.
"""

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _load_local_env():
    """Load simple KEY=VALUE pairs from local .env without external dependencies."""

    env_file = BASE_DIR / ".env"

    if not env_file.exists():
        return

    for raw_line in env_file.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines():

        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]

        if key and key not in __import__("os").environ:
            __import__("os").environ[key] = value


_load_local_env()

def _optional_int(name: str):
    value = os.getenv(name)
    if value in (None, ""):
        return None

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer, got: {value!r}"
        ) from exc


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    app_name: str
    app_env: str
    log_level: str

    bot_token: str | None
    admin_id: int | None

    db_file: Path

    openai_api_key: str | None
    openai_model: str

    session_timeout_minutes: int
    max_ai_tool_calls: int

    default_country: str
    default_currency: str


def load_settings() -> Settings:
    """Load and validate application configuration."""

    db_file = Path(
        os.getenv("DB_FILE", "data/kosfintech.db")
    )

    if not db_file.is_absolute():
        db_file = BASE_DIR / db_file

    return Settings(
        app_name="KOSFintech Global Community Operations Platform",
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),

        bot_token=os.getenv("BOT_TOKEN"),
        admin_id=_optional_int("ADMIN_ID"),

        db_file=db_file,

        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),

        session_timeout_minutes=int(
            os.getenv("SESSION_TIMEOUT_MINUTES", "60")
        ),

        max_ai_tool_calls=int(
            os.getenv("MAX_AI_TOOL_CALLS", "5")
        ),

        default_country=os.getenv("DEFAULT_COUNTRY", "NG"),
        default_currency=os.getenv("DEFAULT_CURRENCY", "NGN"),
    )


settings = load_settings()
