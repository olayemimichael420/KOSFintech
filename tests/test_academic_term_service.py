import sqlite3

import pytest

from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_term_repository import AcademicTermRepository
from services.academic_term_service import AcademicTermService


def _create_service(tenant_id="school-a", connection=None):
    if connection is None:
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
        connection.commit()

    session_repository = AcademicSessionRepository(connection)
    term_repository = AcademicTermRepository(connection)

    session = session_repository.create(
        AcademicSession(
            id=None,
            tenant_id=tenant_id,
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )

    service = AcademicTermService(
        repository=term_repository,
        tenant_id=tenant_id,
    )

    return service, connection, session


def test_create_rejects_tenant_mismatch():
    service, _, session = _create_service()

    term = AcademicTerm(
        id=None,
        tenant_id="school-b",
        academic_session_id=session.id,
        name="First Term",
        start_date="2026-09-01",
        end_date="2026-12-20",
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(term)


def test_create_rejects_invalid_date_range():
    service, _, session = _create_service()

    term = AcademicTerm(
        id=None,
        tenant_id="school-a",
        academic_session_id=session.id,
        name="First Term",
        start_date="2026-12-21",
        end_date="2026-09-01",
    )

    with pytest.raises(
        ValueError,
        match="start date must not be after end date",
    ):
        service.create(term)


def test_create_rejects_missing_session():
    service, _, _ = _create_service()

    term = AcademicTerm(
        id=None,
        tenant_id="school-a",
        academic_session_id=9999,
        name="First Term",
        start_date="2026-09-01",
        end_date="2026-12-20",
    )

    with pytest.raises(ValueError, match="academic session not found"):
        service.create(term)


def test_create_delegates_valid_term():
    service, _, session = _create_service()

    term = AcademicTerm(
        id=None,
        tenant_id="school-a",
        academic_session_id=session.id,
        name="First Term",
        start_date="2026-09-01",
        end_date="2026-12-20",
    )

    created = service.create(term)

    assert created.id is not None
    assert created.tenant_id == "school-a"
    assert created.academic_session_id == session.id
    assert created.name == "First Term"


def test_list_is_session_and_tenant_scoped():
    service, connection, session = _create_service()

    other_service, _, other_session = _create_service(
        tenant_id="school-b",
        connection=connection,
    )

    service.create(
        AcademicTerm(
            id=None,
            tenant_id="school-a",
            academic_session_id=session.id,
            name="First Term",
            start_date="2026-09-01",
            end_date="2026-12-20",
        )
    )

    other_service.create(
        AcademicTerm(
            id=None,
            tenant_id="school-b",
            academic_session_id=other_session.id,
            name="First Term",
            start_date="2026-09-01",
            end_date="2026-12-20",
        )
    )

    terms = service.list(session.id)

    assert len(terms) == 1
    assert terms[0].tenant_id == "school-a"
    assert terms[0].academic_session_id == session.id


def test_get_is_tenant_scoped():
    service, connection, _ = _create_service()

    other_service, _, other_session = _create_service(
        tenant_id="school-b",
        connection=connection,
    )

    term = other_service.create(
        AcademicTerm(
            id=None,
            tenant_id="school-b",
            academic_session_id=other_session.id,
            name="First Term",
            start_date="2026-09-01",
            end_date="2026-12-20",
        )
    )

    assert service.get(term.id) is None
