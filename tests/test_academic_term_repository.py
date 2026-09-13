import sqlite3

from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_term_repository import AcademicTermRepository


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

    connection.execute(
        """
        CREATE TABLE academic_terms (
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
        CREATE UNIQUE INDEX ux_academic_terms_id_tenant
        ON academic_terms(id, tenant_id)
        """
    )

    return connection


def _create_session(connection, tenant_id):
    connection.execute(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_id, f"School {tenant_id}", "Secondary", "Nigeria", "NGN"),
    )

    repository = AcademicSessionRepository(connection)

    session = AcademicSession(
        id=None,
        tenant_id=tenant_id,
        name="2026/2027 Academic Session",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )

    return repository.create(session)


def test_create_and_get_academic_term():
    connection = _connection()
    session = _create_session(connection, "school-001")

    repository = AcademicTermRepository(connection)

    term = AcademicTerm(
        id=None,
        tenant_id="school-001",
        academic_session_id=session.id,
        name="First Term",
        start_date="2026-09-01",
        end_date="2026-12-18",
    )

    repository.create(term)

    assert term.id is not None

    result = repository.get("school-001", term.id)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.academic_session_id == session.id
    assert result.name == "First Term"
    assert result.start_date == "2026-09-01"
    assert result.end_date == "2026-12-18"
    assert result.status == "active"

    connection.close()


def test_academic_term_get_is_tenant_scoped():
    connection = _connection()
    session_one = _create_session(connection, "school-001")
    _create_session(connection, "school-002")

    repository = AcademicTermRepository(connection)

    term = AcademicTerm(
        id=None,
        tenant_id="school-001",
        academic_session_id=session_one.id,
        name="First Term",
        start_date="2026-09-01",
        end_date="2026-12-18",
    )

    repository.create(term)

    assert repository.get("school-001", term.id) is not None
    assert repository.get("school-002", term.id) is None

    connection.close()


def test_academic_term_list_is_scoped_to_session_and_tenant():
    connection = _connection()
    session_one = _create_session(connection, "school-001")
    session_two = _create_session(connection, "school-002")

    repository = AcademicTermRepository(connection)

    repository.create(
        AcademicTerm(
            id=None,
            tenant_id="school-001",
            academic_session_id=session_one.id,
            name="First Term",
            start_date="2026-09-01",
            end_date="2026-12-18",
        )
    )

    repository.create(
        AcademicTerm(
            id=None,
            tenant_id="school-001",
            academic_session_id=session_one.id,
            name="Second Term",
            start_date="2027-01-11",
            end_date="2027-04-09",
        )
    )

    repository.create(
        AcademicTerm(
            id=None,
            tenant_id="school-002",
            academic_session_id=session_two.id,
            name="First Term",
            start_date="2026-09-01",
            end_date="2026-12-18",
        )
    )

    results = repository.list("school-001", session_one.id)

    assert [term.name for term in results] == ["First Term", "Second Term"]

    connection.close()


def test_session_exists_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

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

    connection.executemany(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("school-a", "School A", "secondary", "Nigeria", "NGN"),
            ("school-b", "School B", "secondary", "Nigeria", "NGN"),
        ],
    )

    connection.execute(
        """
        INSERT INTO academic_sessions (
            tenant_id, name, start_date, end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "school-a",
            "2026/2027",
            "2026-09-01",
            "2027-07-31",
        ),
    )
    connection.commit()

    repository = AcademicTermRepository(connection)

    session_id = connection.execute(
        """
        SELECT id
        FROM academic_sessions
        WHERE tenant_id = ?
        """,
        ("school-a",),
    ).fetchone()["id"]

    assert repository.session_exists("school-a", session_id) is True
    assert repository.session_exists("school-b", session_id) is False
