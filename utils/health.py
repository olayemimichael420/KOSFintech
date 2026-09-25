"""Application health and readiness helpers."""

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
