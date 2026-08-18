"""
Database foundation.

Provides the SQLite connection and initializes the core
application schema.
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
    """Initialize the core database schema."""

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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schools (
                tenant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                school_type TEXT NOT NULL,
                country TEXT NOT NULL,
                currency TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                qualification TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER,
                name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                age INTEGER,
                guardian_id INTEGER,
                enrollment_date DATE,
                status TEXT DEFAULT 'active'
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_students (
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (teacher_id, student_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_teachers (
                tenant_id TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, teacher_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_students (
                tenant_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, student_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_schools (
                tenant_id TEXT NOT NULL,
                parent_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, parent_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
            """
        )

        connection.commit()

    finally:
        connection.close()
