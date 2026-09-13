import sqlite3

from models.academic_session import AcademicSession
from repositories.academic_session_repository import AcademicSessionRepository


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE schools (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            school_type TEXT NOT NULL,
            country TEXT NOT NULL,
            currency TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE academic_sessions (
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
        CREATE UNIQUE INDEX ux_academic_sessions_id_tenant
        ON academic_sessions(id, tenant_id)
        """
    )

    return connection


def test_create_and_get_academic_session():
    connection = _connection()

    connection.execute(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("school-001", "KOS Community School", "Secondary", "Nigeria", "NGN"),
    )

    repository = AcademicSessionRepository(connection)

    session = AcademicSession(
        id=None,
        tenant_id="school-001",
        name="2026/2027 Academic Session",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )

    repository.create(session)

    assert session.id is not None

    result = repository.get("school-001", session.id)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.name == "2026/2027 Academic Session"
    assert result.start_date == "2026-09-01"
    assert result.end_date == "2027-07-31"
    assert result.status == "active"

    connection.close()


def test_academic_session_get_is_tenant_scoped():
    connection = _connection()

    connection.executemany(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("school-001", "School One", "Secondary", "Nigeria", "NGN"),
            ("school-002", "School Two", "Secondary", "Nigeria", "NGN"),
        ],
    )

    repository = AcademicSessionRepository(connection)

    session = AcademicSession(
        id=None,
        tenant_id="school-001",
        name="2026/2027 Academic Session",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )

    repository.create(session)

    assert repository.get("school-001", session.id) is not None
    assert repository.get("school-002", session.id) is None

    connection.close()
