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
