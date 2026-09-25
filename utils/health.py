"""Application health and readiness helpers."""

from config import settings
from database import get_connection


def health_status() -> dict:
    """Return application and database health information."""
    connection = get_connection()
    try:
        connection.execute("SELECT 1").fetchone()
    finally:
        connection.close()

    return {
        "status": "ok",
        "component": "kosfintech-foundation",
        "database": "ok",
    }


def readiness_status() -> dict:
    """Return minimum application readiness information."""
    health = health_status()
    bot_token_configured = bool(settings.bot_token)

    return {
        "status": "ready" if health["status"] == "ok" and bot_token_configured else "not_ready",
        "database": health.get("database", "unknown"),
        "bot_token": "configured" if bot_token_configured else "missing",
    }
