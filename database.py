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
    connection.execute("PRAGMA foreign_keys = ON")

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
            CREATE TABLE IF NOT EXISTS administrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                administration_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id)
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
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (guardian_id) REFERENCES parents(id)
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
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_students (
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (teacher_id, student_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_teachers (
                tenant_id TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, teacher_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_students (
                tenant_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, student_id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_schools (
                tenant_id TEXT NOT NULL,
                parent_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, parent_id),
                FOREIGN KEY (parent_id) REFERENCES parents(id)
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_schools (
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, user_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('owner', 'admin1', 'admin2')),
                phone TEXT NOT NULL UNIQUE,
                email TEXT,
                verified BOOLEAN DEFAULT 0,
                verification_code TEXT,
                code_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES schools(tenant_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_authorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('super_admin')),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transferred_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_platform_authorities_active_role
            ON platform_authorities(role)
            WHERE status = 'active'
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_platform_authorities_active_user
            ON platform_authorities(user_id)
            WHERE status = 'active'
            """
        )


        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_administrations_id_tenant
            ON administrations(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_users_id_tenant
            ON users(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS administration_authorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                administration_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('owner', 'admin1', 'admin2')),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(administration_id, role),
                UNIQUE(administration_id, user_id),

                FOREIGN KEY (administration_id, tenant_id)
                    REFERENCES administrations(id, tenant_id),

                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                UNIQUE(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, user_id, role_id),
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id),
                FOREIGN KEY (role_id, tenant_id)
                    REFERENCES roles(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                UNIQUE(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                tenant_id TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, role_id, permission_id),
                FOREIGN KEY (role_id, tenant_id)
                    REFERENCES roles(id, tenant_id),
                FOREIGN KEY (permission_id, tenant_id)
                    REFERENCES permissions(id, tenant_id)
            )
            """
        )

        connection.commit()

    finally:
        connection.close()
