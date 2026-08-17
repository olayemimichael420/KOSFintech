#!/usr/bin/env python3
"""
KOSFintech Global Community Operations Platform
PART 1 — Project Foundation

Purpose:
    Establish the production project structure without disturbing
    the preserved legacy implementation.

This file is a project-generation script.
It creates the architectural directories and foundational files.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent


DIRECTORIES = [
    "models",
    "services",
    "handlers",
    "utils",
    "ai",
    "ai/providers",
    "tests",
    "docs",
    "data",
    "scripts",
    "legacy",
]


FILES = {
    "requirements.txt": """\
python-telegram-bot>=22.8,<23
python-dotenv>=1.0,<2
pytest>=8,<9
pytest-asyncio>=0.24,<2
httpx>=0.27,<1
openai>=1.0,<2
""",

    ".env.example": """\
# KOSFintech environment configuration
# NEVER commit the real .env file.

BOT_TOKEN=
ADMIN_ID=

# AI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Database
DB_FILE=data/kosfintech.db

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Security
SESSION_TIMEOUT_MINUTES=60
MAX_AI_TOOL_CALLS=5

# Global/community defaults
DEFAULT_COUNTRY=NG
DEFAULT_CURRENCY=NGN
""",

    "config.py": '''\
"""
KOSFintech configuration layer.

All environment-dependent configuration is centralized here.
Business logic must not read environment variables directly.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# Load local .env when present.
load_dotenv(BASE_DIR / ".env")


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
''',

    "bot.py": '''\
#!/usr/bin/env python3
"""
KOSFintech Telegram application entry point.

PART 1 intentionally keeps the Telegram entry point minimal.
Business logic will be introduced through handlers/services in
subsequent development parts.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import settings


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("kosfintech")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic health/start command."""

    await update.message.reply_text(
        "🚀 KOSFintech Global Community Operations Platform\\n\\n"
        "Foundation layer is online.\\n"
        "The modular system is being assembled incrementally.\\n\\n"
        "Use /health to verify the application."
    )


async def health(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Basic application health response."""

    await update.message.reply_text(
        "✅ KOSFintech application is responding.\\n"
        f"Environment: {settings.app_env}"
    )


def build_application() -> Application:
    """Construct the Telegram application."""

    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not configured. "
            "Set it in the environment or .env file."
        )

    application = (
        Application.builder()
        .token(settings.bot_token)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("health", health)
    )

    return application


def main() -> None:
    """Application entry point."""

    logger.info("Starting KOSFintech foundation...")

    application = build_application()

    logger.info(
        "KOSFintech Telegram application started."
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
''',

    "models/__init__.py": '''\
"""KOSFintech domain models."""
''',

    "services/__init__.py": '''\
"""KOSFintech business services."""
''',

    "handlers/__init__.py": '''\
"""KOSFintech Telegram handlers."""
''',

    "utils/__init__.py": '''\
"""KOSFintech utility functions."""
''',

    "ai/__init__.py": '''\
"""KOSFintech artificial intelligence layer."""
''',

    "ai/providers/__init__.py": '''\
"""Provider adapters for the KOSFintech AI layer."""
''',

    "tests/__init__.py": '''\
"""KOSFintech test package."""
''',

    "database.py": '''\
"""
Database foundation.

Business-specific tables and repositories will be introduced
in later development parts.
"""

import sqlite3
from pathlib import Path

from config import settings


def get_db_path() -> Path:
    """Return the configured database path."""

    settings.db_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return settings.db_file


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection."""

    connection = sqlite3.connect(
        get_db_path(),
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_db() -> None:
    """Initialize the database foundation."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()
''',

    "auth.py": '''\
"""
Authentication and authorization foundation.

Full RBAC and tenant isolation will be implemented in the
authentication phase.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserContext:
    """Security context for an authenticated user."""

    user_id: int
    tenant_id: Optional[str]
    role: str
    is_authenticated: bool = True


def authorize(
    user: UserContext,
    permission: str,
) -> bool:
    """
    Foundation authorization hook.

    The complete permission matrix will be implemented later.
    """

    if not user.is_authenticated:
        return False

    if user.role == "super_admin":
        return True

    return permission == "public.read"
''',

    "audit.py": '''\
"""
Audit logging foundation.

All consequential operations, including AI-driven actions,
will eventually be recorded here.
"""

import json
import logging
from datetime import datetime, timezone


logger = logging.getLogger("kosfintech.audit")


def audit_event(
    event_type: str,
    actor_id=None,
    tenant_id=None,
    action=None,
    metadata=None,
) -> None:
    """Record a structured audit event."""

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "tenant_id": tenant_id,
        "action": action,
        "metadata": metadata or {},
    }

    logger.info(
        "AUDIT %s",
        json.dumps(event, default=str),
    )
''',

    "utils/health.py": '''\
"""Basic application health helpers."""


def health_status() -> dict:
    """Return basic application health information."""

    return {
        "status": "ok",
        "component": "kosfintech-foundation",
    }
''',

    "tests/test_foundation.py": '''\
from pathlib import Path

from config import settings
from database import get_db_path, init_db
from utils.health import health_status


def test_settings_load():
    assert settings.app_name.startswith("KOSFintech")
    assert settings.default_country
    assert settings.default_currency


def test_database_path():
    path = get_db_path()

    assert isinstance(path, Path)
    assert path.parent.exists()


def test_database_initialization():
    init_db()

    assert get_db_path().exists()


def test_health():
    result = health_status()

    assert result["status"] == "ok"
''',

    "docs/ARCHITECTURE.md": '''\
# KOSFintech Architecture

## Current Phase

Part 1 — Project Foundation.

## Architectural principle

The system is being migrated from the historical monolithic Telegram
implementation into a modular global community operations platform.

## Core layers

- Configuration
- Database
- Authentication
- Audit
- Domain models
- Business services
- Telegram handlers
- AI intelligence
- AI provider adapters
- Utilities
- Tests
- DevOps

## Legacy preservation

Historical implementations are preserved separately and are not
automatically imported into the production execution path.

They are migration references.

## Global architecture

The system is designed around tenant isolation so that the same
application architecture can support:

- individual communities
- schools
- organizations
- regional deployments
- national deployments
- global operations

without hard-coding the application to one geographic deployment.

## Security principle

No AI-generated action should bypass normal authorization,
tenant isolation, validation, auditing, or confirmation requirements.
''',

    "README.md": '''\
# KOSFintech

Global Community Operations Platform.

This repository is being migrated from a historical monolithic
Telegram bot into a modular, tenant-aware architecture.

Development is incremental.

See `docs/ARCHITECTURE.md` for the current architectural direction.
''',
}


def create_directories() -> None:
    for directory in DIRECTORIES:
        path = ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"[DIR]  {path.relative_to(ROOT)}")


def create_files() -> None:
    for filename, content in FILES.items():
        path = ROOT / filename

        # Do not overwrite an existing non-empty file accidentally.
        if path.exists() and path.stat().st_size > 0:
            print(f"[SKIP] {filename} already exists")
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        print(f"[FILE] {filename}")


def main() -> None:
    print("=" * 60)
    print("KOSFintech PART 1 — Foundation")
    print("=" * 60)

    create_directories()
    create_files()

    print()
    print("Foundation generation complete.")
    print()
    print("Next:")
    print("  python -m pytest")
    print("  python -m py_compile config.py database.py auth.py audit.py bot.py")
    print()


if __name__ == "__main__":
    main()
