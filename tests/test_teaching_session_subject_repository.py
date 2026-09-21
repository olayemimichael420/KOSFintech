import sqlite3

import pytest

from models.teaching_session import TeachingSession
from models.teaching_session_subject import TeachingSessionSubject
from models.teaching_subject import TeachingSubject
from repositories.teaching_session_repository import TeachingSessionRepository
from repositories.teaching_session_subject_repository import (
    TeachingSessionSubjectRepository,
)
from repositories.teaching_subject_repository import TeachingSubjectRepository


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _create_session(connection, tenant_id, name="Session"):
    return TeachingSessionRepository(connection).create(
        TeachingSession(
            id=None,
            tenant_id=tenant_id,
            name=name,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
    )


def _create_subject(connection, tenant_id, name="Faith"):
    return TeachingSubjectRepository(connection).create(
        TeachingSubject(
            id=None,
            tenant_id=tenant_id,
            name=name,
        )
    )


def test_create_get_and_list_round_trip(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    session = _create_session(connection, "tenant-001")
    subject = _create_subject(connection, "tenant-001")

    repository = TeachingSessionSubjectRepository(connection)

    offering = TeachingSessionSubject(
        id=None,
        tenant_id="tenant-001",
        teaching_session_id=session.id,
        teaching_subject_id=subject.id,
    )

    created = repository.create(offering)

    assert created.id is not None
    assert created.tenant_id == "tenant-001"
    assert created.teaching_session_id == session.id
    assert created.teaching_subject_id == subject.id
    assert created.status == "active"

    assert repository.get("tenant-001", created.id) == created
    assert repository.list("tenant-001", session.id) == [created]


def test_get_and_list_are_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-a")
    _create_tenant(connection, "tenant-b")

    session = _create_session(connection, "tenant-a")
    subject = _create_subject(connection, "tenant-a")

    repository = TeachingSessionSubjectRepository(connection)

    offering = repository.create(
        TeachingSessionSubject(
            id=None,
            tenant_id="tenant-a",
            teaching_session_id=session.id,
            teaching_subject_id=subject.id,
        )
    )

    assert repository.get("tenant-a", offering.id) == offering
    assert repository.get("tenant-b", offering.id) is None
    assert repository.list("tenant-a", session.id) == [offering]
    assert repository.list("tenant-b", session.id) == []


def test_duplicate_session_subject_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    session = _create_session(connection, "tenant-001")
    subject = _create_subject(connection, "tenant-001")

    repository = TeachingSessionSubjectRepository(connection)

    offering = TeachingSessionSubject(
        id=None,
        tenant_id="tenant-001",
        teaching_session_id=session.id,
        teaching_subject_id=subject.id,
    )

    repository.create(offering)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(offering)


def test_same_session_subject_pair_is_allowed_in_different_tenants(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-a")
    _create_tenant(connection, "tenant-b")

    session_a = _create_session(connection, "tenant-a", "Session A")
    subject_a = _create_subject(connection, "tenant-a", "Faith A")

    session_b = _create_session(connection, "tenant-b", "Session B")
    subject_b = _create_subject(connection, "tenant-b", "Faith B")

    repository = TeachingSessionSubjectRepository(connection)

    first = repository.create(
        TeachingSessionSubject(
            id=None,
            tenant_id="tenant-a",
            teaching_session_id=session_a.id,
            teaching_subject_id=subject_a.id,
        )
    )

    second = repository.create(
        TeachingSessionSubject(
            id=None,
            tenant_id="tenant-b",
            teaching_session_id=session_b.id,
            teaching_subject_id=subject_b.id,
        )
    )

    assert first.id != second.id
    assert repository.get("tenant-a", first.id) == first
    assert repository.get("tenant-b", second.id) == second


def test_cross_tenant_parent_reference_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-a")
    _create_tenant(connection, "tenant-b")

    session_a = _create_session(connection, "tenant-a")
    subject_b = _create_subject(connection, "tenant-b")

    repository = TeachingSessionSubjectRepository(connection)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            TeachingSessionSubject(
                id=None,
                tenant_id="tenant-a",
                teaching_session_id=session_a.id,
                teaching_subject_id=subject_b.id,
            )
        )
