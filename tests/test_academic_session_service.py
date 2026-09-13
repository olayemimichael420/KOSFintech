import sqlite3

import pytest

from models.academic_session import AcademicSession
from repositories.academic_session_repository import AcademicSessionRepository
from services.academic_session_service import AcademicSessionService


def _create_service(tenant_id="school-a", user_id=None, connection=None):
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
                currency TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                "Test School",
                "secondary",
                "Nigeria",
                "NGN",
            ),
        )
        connection.commit()

    existing_school = connection.execute(
        "SELECT 1 FROM schools WHERE tenant_id = ?",
        (tenant_id,),
    ).fetchone()

    if existing_school is None:
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                "Test School",
                "secondary",
                "Nigeria",
                "NGN",
            ),
        )
        connection.commit()

    repository = AcademicSessionRepository(connection)

    return (
        AcademicSessionService(
            repository=repository,
            tenant_id=tenant_id,
            connection=None,
            user_id=user_id,
        ),
        connection,
    )


def test_create_rejects_tenant_mismatch():
    service, _ = _create_service()

    session = AcademicSession(
        id=None,
        tenant_id="school-b",
        name="2026/2027",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(session)


def test_create_rejects_invalid_date_range():
    service, _ = _create_service()

    session = AcademicSession(
        id=None,
        tenant_id="school-a",
        name="2026/2027",
        start_date="2027-08-01",
        end_date="2027-07-31",
    )

    with pytest.raises(
        ValueError,
        match="start date must not be after end date",
    ):
        service.create(session)


def test_create_delegates_valid_session():
    service, _ = _create_service()

    session = AcademicSession(
        id=None,
        tenant_id="school-a",
        name="2026/2027",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )

    created = service.create(session)

    assert created.id is not None
    assert created.tenant_id == "school-a"
    assert created.name == "2026/2027"


def test_list_is_tenant_scoped():
    service, connection = _create_service()

    other_service, _ = _create_service(
        tenant_id="school-b",
        connection=connection,
    )

    service.create(
        AcademicSession(
            id=None,
            tenant_id="school-a",
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )

    other_service.create(
        AcademicSession(
            id=None,
            tenant_id="school-b",
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )

    sessions = service.list()

    assert len(sessions) == 1
    assert sessions[0].tenant_id == "school-a"


def test_get_is_tenant_scoped():
    service, connection = _create_service()

    other_service, _ = _create_service(
        tenant_id="school-b",
        connection=connection,
    )

    session = other_service.create(
        AcademicSession(
            id=None,
            tenant_id="school-b",
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )

    assert service.get(session.id) is None
