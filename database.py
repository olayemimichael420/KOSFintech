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


def _migrate_talent_point_transactions(connection: sqlite3.Connection) -> None:
    """Upgrade the legacy Talent Point transaction schema for transfers."""

    table = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'talent_point_transactions'
        """
    ).fetchone()

    if table is None:
        return

    table_sql = table["sql"] or ""

    if (
        "service_act_id INTEGER," in table_sql
        and "CHECK(amount != 0)" in table_sql
        and "CHECK(transaction_type IN ('issuance', 'transfer'))" in table_sql
    ):
        return

    invalid_rows = connection.execute(
        """
        SELECT id
        FROM talent_point_transactions
        WHERE amount <= 0
           OR transaction_type != 'issuance'
           OR service_act_id IS NULL
        LIMIT 1
        """
    ).fetchone()

    if invalid_rows:
        raise RuntimeError(
            "Cannot migrate talent_point_transactions: "
            "existing rows are incompatible with the expected legacy "
            "issuance-only schema."
        )

    connection.execute(
        """
        CREATE TABLE talent_point_transactions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            service_act_id INTEGER,
            amount INTEGER NOT NULL CHECK(amount != 0),
            transaction_type TEXT NOT NULL
                CHECK(transaction_type IN ('issuance', 'transfer')),
            reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id, tenant_id)
                REFERENCES users(id, tenant_id),

            FOREIGN KEY (service_act_id, tenant_id)
                REFERENCES service_acts(id, tenant_id),

            UNIQUE(id, tenant_id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO talent_point_transactions_new (
            id,
            tenant_id,
            user_id,
            service_act_id,
            amount,
            transaction_type,
            reference,
            created_at
        )
        SELECT
            id,
            tenant_id,
            user_id,
            service_act_id,
            amount,
            transaction_type,
            reference,
            created_at
        FROM talent_point_transactions
        """
    )

    connection.execute("DROP TABLE talent_point_transactions")

    connection.execute(
        """
        ALTER TABLE talent_point_transactions_new
        RENAME TO talent_point_transactions
        """
    )


def _create_audit_immutability_triggers(connection: sqlite3.Connection) -> None:
    """Prevent modification or deletion of persisted audit events."""
    connection.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_update
        BEFORE UPDATE ON audit_events
        BEGIN
            SELECT RAISE(ABORT, 'audit_events are immutable');
        END;
    """)

    connection.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_audit_events_no_delete
        BEFORE DELETE ON audit_events
        BEGIN
            SELECT RAISE(ABORT, 'audit_events are immutable');
        END;
    """)


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
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_id INTEGER,
                tenant_id TEXT,
                action TEXT,
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        _create_audit_immutability_triggers(connection)

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_audit_events_tenant_id
            ON audit_events(tenant_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_audit_events_event_type
            ON audit_events(event_type)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_audit_events_timestamp
            ON audit_events(timestamp)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            CREATE TABLE IF NOT EXISTS institution_anchors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_type TEXT NOT NULL,
                name TEXT NOT NULL,
                provenance_reference TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(
                        verification_status IN (
                            'pending',
                            'verified',
                            'rejected'
                        )
                    ),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS service_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_anchor_id INTEGER NOT NULL,
                tenant_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (institution_anchor_id)
                    REFERENCES institution_anchors(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS church_anchors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                provenance_reference TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(
                        verification_status IN (
                            'pending',
                            'verified',
                            'rejected'
                        )
                    ),
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (tenant_id)
                    REFERENCES administrations(tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_channel_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                administration_id INTEGER NOT NULL,
                binding_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (administration_id, tenant_id)
                    REFERENCES administrations(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_telegram_channel_bindings_provider_chat
            ON telegram_channel_bindings(provider, chat_id)
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
            CREATE TABLE IF NOT EXISTS academic_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (tenant_id)
                    REFERENCES schools(tenant_id),
                UNIQUE (tenant_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_academic_sessions_id_tenant
            ON academic_sessions(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS academic_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                academic_session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (academic_session_id, tenant_id)
                    REFERENCES academic_sessions(id, tenant_id),
                UNIQUE (tenant_id, academic_session_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_academic_terms_id_tenant
            ON academic_terms(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS academic_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                education_level TEXT,
                sequence INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (tenant_id)
                    REFERENCES schools(tenant_id),
                UNIQUE (tenant_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_academic_classes_id_tenant
            ON academic_classes(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS academic_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (tenant_id)
                    REFERENCES schools(tenant_id),
                UNIQUE (tenant_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_academic_subjects_id_tenant
            ON academic_subjects(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS course_offerings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                academic_class_id INTEGER NOT NULL,
                academic_subject_id INTEGER NOT NULL,
                academic_session_id INTEGER NOT NULL,
                academic_term_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (academic_class_id, tenant_id)
                    REFERENCES academic_classes(id, tenant_id),
                FOREIGN KEY (academic_subject_id, tenant_id)
                    REFERENCES academic_subjects(id, tenant_id),
                FOREIGN KEY (academic_session_id, tenant_id)
                    REFERENCES academic_sessions(id, tenant_id),
                FOREIGN KEY (academic_term_id, tenant_id)
                    REFERENCES academic_terms(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_course_offerings_id_tenant
            ON course_offerings(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_course_offerings_unique_offering
            ON course_offerings(
                tenant_id,
                academic_class_id,
                academic_subject_id,
                academic_session_id,
                academic_term_id
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS course_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                course_offering_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (course_offering_id, tenant_id)
                    REFERENCES course_offerings(id, tenant_id),
                UNIQUE (tenant_id, course_offering_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_course_sections_id_tenant
            ON course_sections(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS section_student_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                course_section_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (course_section_id, tenant_id)
                    REFERENCES course_sections(id, tenant_id),
                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id),
                UNIQUE (tenant_id, course_section_id, student_id)
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_section_student_enrollments_id_tenant
            ON section_student_enrollments(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS section_teacher_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                course_section_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (course_section_id, tenant_id)
                    REFERENCES course_sections(id, tenant_id),
                FOREIGN KEY (teacher_id, tenant_id)
                    REFERENCES teachers(id, tenant_id),
                UNIQUE (tenant_id, course_section_id, teacher_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_section_teacher_assignments_id_tenant
            ON section_teacher_assignments(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_subject_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                academic_subject_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (teacher_id, tenant_id)
                    REFERENCES teachers(id, tenant_id),
                FOREIGN KEY (academic_subject_id, tenant_id)
                    REFERENCES academic_subjects(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_teacher_subject_assignments_id_tenant
            ON teacher_subject_assignments(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS student_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                academic_class_id INTEGER NOT NULL,
                academic_session_id INTEGER NOT NULL,
                academic_term_id INTEGER,
                enrollment_date DATE,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),

                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id),

                FOREIGN KEY (academic_class_id, tenant_id)
                    REFERENCES academic_classes(id, tenant_id),

                FOREIGN KEY (academic_session_id, tenant_id)
                    REFERENCES academic_sessions(id, tenant_id),

                FOREIGN KEY (academic_term_id, tenant_id)
                    REFERENCES academic_terms(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_student_enrollments_id_tenant
            ON student_enrollments(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_student_enrollments_active_session
            ON student_enrollments(
                tenant_id,
                student_id,
                academic_session_id
            )
            WHERE status = 'active'
              AND academic_term_id IS NULL
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_student_enrollments_active_term
            ON student_enrollments(
                tenant_id,
                student_id,
                academic_session_id,
                academic_term_id
            )
            WHERE status = 'active'
              AND academic_term_id IS NOT NULL
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
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
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
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id),
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
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
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
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                student_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'present',
                remark TEXT,
                FOREIGN KEY (student_id, tenant_id)
                    REFERENCES students(id, tenant_id),
                UNIQUE (tenant_id, student_id, attendance_date)
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS external_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                subject TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_external_identities_provider_subject
            ON external_identities(provider, subject)
            """
        )

        _migrate_user_schools_tenant_fk(connection)
        _migrate_talent_point_transactions(connection)

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
                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
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
            CREATE TABLE IF NOT EXISTS judicial_jurisdictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                jurisdiction_type TEXT NOT NULL,
                jurisdiction_scope TEXT NOT NULL,
                judicial_level TEXT NOT NULL,
                case_types TEXT NOT NULL,
                parent_jurisdiction_id INTEGER,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'inactive')),

                UNIQUE(id, tenant_id),

                FOREIGN KEY (parent_jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_jurisdictions_tenant_status
            ON judicial_jurisdictions(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                candidate_user_id INTEGER NOT NULL,
                jurisdiction_id INTEGER NOT NULL,
                judicial_level TEXT NOT NULL,
                appointment_source TEXT NOT NULL,
                appointment_basis TEXT NOT NULL,
                qualification_record TEXT NOT NULL,
                appointed_by INTEGER NOT NULL,
                appointed_at TIMESTAMP,
                term_start TIMESTAMP,
                term_end TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'appointed',

                UNIQUE(id, tenant_id),

                FOREIGN KEY (candidate_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id),

                FOREIGN KEY (appointed_by, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_appointments_tenant_status
            ON judicial_appointments(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_appointments_candidate
            ON judicial_appointments(tenant_id, candidate_user_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_conferrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                appointment_id INTEGER NOT NULL,
                authority_id INTEGER NOT NULL,
                conferring_authority TEXT NOT NULL,
                conferral_instrument TEXT NOT NULL,
                conferral_date TIMESTAMP,
                effective_from TIMESTAMP,
                effective_until TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'active',

                UNIQUE(id, tenant_id),

                FOREIGN KEY (appointment_id, tenant_id)
                    REFERENCES judicial_appointments(id, tenant_id),

                FOREIGN KEY (authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_conferrals_tenant_status
            ON judicial_conferrals(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_authorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                authority_type TEXT NOT NULL,
                jurisdiction_id INTEGER NOT NULL,
                judicial_level TEXT NOT NULL,
                appointment_id INTEGER NOT NULL,
                conferral_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'proposed'
                    CHECK(
                        status IN (
                            'proposed',
                            'vetted',
                            'appointed',
                            'active',
                            'suspended',
                            'inactive',
                            'revoked',
                            'expired'
                        )
                    ),
                effective_from TIMESTAMP,
                effective_until TIMESTAMP,

                UNIQUE(id, tenant_id),

                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id),

                FOREIGN KEY (appointment_id, tenant_id)
                    REFERENCES judicial_appointments(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_authorities_tenant_status
            ON judicial_authorities(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_authorities_user
            ON judicial_authorities(tenant_id, user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_authorities_jurisdiction
            ON judicial_authorities(tenant_id, jurisdiction_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_proceedings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                dispute_id INTEGER NOT NULL,
                jurisdiction_id INTEGER NOT NULL,
                proceeding_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'proposed'
                  CHECK(status IN (
                    'proposed',
                    'open',
                    'active',
                    'closed',
                    'terminated'
                  )),
                opened_by_authority_id INTEGER,
                opened_at TIMESTAMP,
                closed_at TIMESTAMP,
                closure_reason TEXT,
                UNIQUE(id, tenant_id),
                FOREIGN KEY (dispute_id, tenant_id)
                    REFERENCES disputes(id, tenant_id),
                FOREIGN KEY (jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id),
                FOREIGN KEY (opened_by_authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_proceedings_tenant_status
            ON judicial_proceedings(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_proceedings_tenant_dispute
            ON judicial_proceedings(tenant_id, dispute_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_proceedings_tenant_jurisdiction
            ON judicial_proceedings(tenant_id, jurisdiction_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                proceeding_id INTEGER NOT NULL,
                judicial_authority_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT NOT NULL,
                acted_at TIMESTAMP,
                UNIQUE(id, tenant_id),
                FOREIGN KEY (proceeding_id, tenant_id)
                    REFERENCES judicial_proceedings(id, tenant_id),
                FOREIGN KEY (judicial_authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_actions_tenant_proceeding
            ON judicial_actions(tenant_id, proceeding_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_actions_tenant_authority
            ON judicial_actions(tenant_id, judicial_authority_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                proceeding_id INTEGER NOT NULL,
                judicial_authority_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                decision_reason TEXT NOT NULL,
                decided_at TIMESTAMP,
                UNIQUE(id, tenant_id),
                FOREIGN KEY (proceeding_id, tenant_id)
                    REFERENCES judicial_proceedings(id, tenant_id),
                FOREIGN KEY (judicial_authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_decisions_tenant_proceeding
            ON judicial_decisions(tenant_id, proceeding_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_decisions_tenant_authority
            ON judicial_decisions(tenant_id, judicial_authority_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                proceeding_id INTEGER NOT NULL,
                decision_id INTEGER NOT NULL,
                originating_judicial_authority_id INTEGER NOT NULL,
                jurisdiction_id INTEGER NOT NULL,
                review_type TEXT NOT NULL
                    CHECK(review_type IN (
                        'review',
                        'appeal'
                    )),
                initiated_by INTEGER NOT NULL,
                grounds TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'proposed'
                    CHECK(status IN (
                        'proposed'
                    )),
                recorded_at TIMESTAMP,
                UNIQUE(id, tenant_id),
                FOREIGN KEY (proceeding_id, tenant_id)
                    REFERENCES judicial_proceedings(id, tenant_id),
                FOREIGN KEY (decision_id, tenant_id)
                    REFERENCES judicial_decisions(id, tenant_id),
                FOREIGN KEY (originating_judicial_authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id),
                FOREIGN KEY (jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id),
                FOREIGN KEY (initiated_by, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_reviews_tenant_proceeding
            ON judicial_reviews(tenant_id, proceeding_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_reviews_tenant_decision
            ON judicial_reviews(tenant_id, decision_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_reviews_tenant_authority
            ON judicial_reviews(tenant_id, originating_judicial_authority_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_reviews_tenant_jurisdiction
            ON judicial_reviews(tenant_id, jurisdiction_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_reviews_tenant_status
            ON judicial_reviews(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judicial_recusals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                judicial_authority_id INTEGER NOT NULL,
                jurisdiction_id INTEGER NOT NULL,
                proceeding_id INTEGER,
                scope TEXT NOT NULL
                    CHECK(scope IN (
                        'jurisdiction',
                        'proceeding'
                    )),
                reason TEXT NOT NULL,
                initiated_by INTEGER NOT NULL,
                recorded_at TIMESTAMP,
                resolved_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN (
                        'active',
                        'resolved'
                    )),
                UNIQUE(id, tenant_id),
                FOREIGN KEY (judicial_authority_id, tenant_id)
                    REFERENCES judicial_authorities(id, tenant_id),
                FOREIGN KEY (jurisdiction_id, tenant_id)
                    REFERENCES judicial_jurisdictions(id, tenant_id),
                FOREIGN KEY (proceeding_id, tenant_id)
                    REFERENCES judicial_proceedings(id, tenant_id),
                FOREIGN KEY (initiated_by, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_recusals_tenant_status
            ON judicial_recusals(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_recusals_tenant_authority
            ON judicial_recusals(tenant_id, judicial_authority_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_recusals_tenant_jurisdiction
            ON judicial_recusals(tenant_id, jurisdiction_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_judicial_recusals_tenant_proceeding
            ON judicial_recusals(tenant_id, proceeding_id)
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
            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                requester_user_id INTEGER NOT NULL,
                recipient_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'requested'
                    CHECK(
                        status IN (
                            'requested',
                            'authorized',
                            'cancelled'
                        )
                    ),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                authorized_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                cancellation_reason TEXT,

                FOREIGN KEY (requester_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (recipient_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                CHECK(requester_user_id != recipient_user_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_service_requests_id_tenant
            ON service_requests(id, tenant_id)
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
            CREATE TABLE IF NOT EXISTS reputation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                service_act_id INTEGER NOT NULL,
                subject_user_id INTEGER NOT NULL,
                reviewer_user_id INTEGER NOT NULL,
                score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (service_act_id, tenant_id)
                    REFERENCES service_acts(id, tenant_id),

                FOREIGN KEY (subject_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (reviewer_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                UNIQUE(service_act_id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_reputation_events_tenant_subject
            ON reputation_events(tenant_id, subject_user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_reputation_events_tenant_reviewer
            ON reputation_events(tenant_id, reviewer_user_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS talent_point_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                service_act_id INTEGER,
                amount INTEGER NOT NULL CHECK(amount != 0),
                transaction_type TEXT NOT NULL
                    CHECK(transaction_type IN ('issuance', 'transfer')),
                reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id, tenant_id)
                    REFERENCES users(id, tenant_id),

                FOREIGN KEY (service_act_id, tenant_id)
                    REFERENCES service_acts(id, tenant_id),

                UNIQUE(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_talent_point_transactions_tenant_user
            ON talent_point_transactions(tenant_id, user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_talent_point_transactions_tenant_act
            ON talent_point_transactions(tenant_id, service_act_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_talent_point_transactions_tenant_type
            ON talent_point_transactions(tenant_id, transaction_type)
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_talent_point_issuance_service_act
            ON talent_point_transactions(tenant_id, service_act_id)
            WHERE transaction_type = 'issuance'
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS disputes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                service_act_id INTEGER NOT NULL,
                initiator_user_id INTEGER NOT NULL,
                initiator_role TEXT NOT NULL
                    CHECK(initiator_role IN ('provider', 'recipient')),
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
                    CHECK(status IN (
                        'open',
                        'under_review',
                        'resolved',
                        'rejected',
                        'withdrawn'
                    )),
                resolution TEXT
                    CHECK(resolution IS NULL OR resolution IN (
                        'provider_favored',
                        'recipient_favored',
                        'mutual_settlement',
                        'no_fault'
                    )),
                resolution_reason TEXT,
                resolved_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (service_act_id, tenant_id)
                    REFERENCES service_acts(id, tenant_id),
                FOREIGN KEY (initiator_user_id, tenant_id)
                    REFERENCES users(id, tenant_id),
                FOREIGN KEY (resolved_by_user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            ux_disputes_id_tenant
            ON disputes(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_disputes_tenant_status
            ON disputes(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_disputes_tenant_service_act
            ON disputes(tenant_id, service_act_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_disputes_tenant_initiator
            ON disputes(tenant_id, initiator_user_id)
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governance_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                proposer_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK(status IN ('draft', 'open', 'closed', 'cancelled')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                opened_at TEXT,
                closed_at TEXT,
                UNIQUE(id, tenant_id),
                FOREIGN KEY (proposer_user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_governance_proposals_tenant_status
            ON governance_proposals(tenant_id, status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_governance_proposals_proposer
            ON governance_proposals(tenant_id, proposer_user_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governance_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                proposal_id INTEGER NOT NULL,
                voter_user_id INTEGER NOT NULL,
                choice TEXT NOT NULL
                    CHECK(choice IN ('yes', 'no', 'abstain')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(id, tenant_id),
                UNIQUE(tenant_id, proposal_id, voter_user_id),
                FOREIGN KEY (proposal_id, tenant_id)
                    REFERENCES governance_proposals(id, tenant_id),
                FOREIGN KEY (voter_user_id, tenant_id)
                    REFERENCES users(id, tenant_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_governance_votes_proposal
            ON governance_votes(tenant_id, proposal_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_governance_votes_voter
            ON governance_votes(tenant_id, voter_user_id)
            """
        )

        connection.commit()

    finally:
        connection.close()

# Service Act schema
# Added during Phase 3: Service Act Engine.
