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



def _migrate_user_schools_tenant_fk(connection: sqlite3.Connection) -> None:
    """Upgrade legacy user_schools FK to tenant-scoped composite FK."""

    table = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'user_schools'
        """
    ).fetchone()

    if table is None:
        return

    table_sql = table["sql"] or ""

    if "FOREIGN KEY (user_id, tenant_id)" in table_sql:
        return

    invalid_rows = connection.execute(
        """
        SELECT
            us.tenant_id,
            us.user_id,
            u.tenant_id AS user_tenant
        FROM user_schools AS us
        LEFT JOIN users AS u
            ON u.id = us.user_id
        WHERE u.id IS NULL
           OR us.tenant_id != u.tenant_id
        """
    ).fetchall()

    if invalid_rows:
        raise RuntimeError(
            "Cannot migrate user_schools: existing rows contain "
            "invalid or cross-tenant user relationships."
        )

    connection.execute(
        """
        CREATE TABLE user_schools_new (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id),
            FOREIGN KEY (user_id, tenant_id)
                REFERENCES users(id, tenant_id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO user_schools_new (tenant_id, user_id)
        SELECT tenant_id, user_id
        FROM user_schools
        """
    )

    connection.execute("DROP TABLE user_schools")

    connection.execute(
        """
        ALTER TABLE user_schools_new
        RENAME TO user_schools
        """
    )


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
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_teachers_id_tenant
            ON teachers(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_students_id_tenant
            ON students(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_parents_id_tenant
            ON parents(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_students (
                tenant_id TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, teacher_id, student_id),
                FOREIGN KEY (teacher_id, tenant_id)
                    REFERENCES teachers(id, tenant_id),
                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_students (
                tenant_id TEXT NOT NULL,
                parent_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, parent_id, student_id),
                FOREIGN KEY (parent_id, tenant_id)
                    REFERENCES parents(id, tenant_id),
                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_teachers (
                tenant_id TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, teacher_id),
                FOREIGN KEY (teacher_id, tenant_id)
                    REFERENCES teachers(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS school_students (
                tenant_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, student_id),
                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_schools (
                tenant_id TEXT NOT NULL,
                parent_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, parent_id),
                FOREIGN KEY (parent_id, tenant_id)
                    REFERENCES parents(id, tenant_id)
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
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_users_id_tenant
            ON users(id, tenant_id)
            """
        )

        _migrate_user_schools_tenant_fk(connection)

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_schools (
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, user_id),
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
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


                FOREIGN KEY (administration_id, tenant_id)
                    REFERENCES administrations(id, tenant_id),

                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_administration_authorities_active_role
            ON administration_authorities(administration_id, role)
            WHERE status = 'active'
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_administration_authorities_active_user
            ON administration_authorities(administration_id, user_id)
            WHERE status = 'active'
            """
        )


        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS service_acts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                provider_user_id INTEGER NOT NULL,
                recipient_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created'
                    CHECK(
                        status IN (
                            'created',
                            'accepted',
                            'in_progress',
                            'submitted',
                            'completed',
                            'cancelled'
                        )
                    ),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                started_at TIMESTAMP,
                submitted_at TIMESTAMP,
                completed_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                cancellation_reason TEXT,

                FOREIGN KEY (provider_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (recipient_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                CHECK(provider_user_id != recipient_user_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_service_acts_id_tenant
            ON service_acts(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_service_acts_tenant_status
            ON service_acts(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_service_acts_provider
            ON service_acts(tenant_id, provider_user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_service_acts_recipient
            ON service_acts(tenant_id, recipient_user_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                service_act_id INTEGER NOT NULL,
                verifier_user_id INTEGER NOT NULL,
                decision TEXT NOT NULL
                    CHECK(decision IN ('approved', 'rejected')),
                reason TEXT,

                FOREIGN KEY (service_act_id, tenant_id)
                    REFERENCES service_acts(id, tenant_id),

                FOREIGN KEY (verifier_user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_verifications_verifier_act
            ON verifications(tenant_id, service_act_id, verifier_user_id)
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

# Service Act schema
# Added during Phase 3: Service Act Engine.
