import sqlite3

import pytest

from models.person import Person
from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from models.teaching_session import TeachingSession
from models.session_teacher_preacher_assignment import (
    SessionTeacherPreacherAssignment,
)
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from repositories.teaching_session_repository import TeachingSessionRepository
from repositories.session_teacher_preacher_assignment_repository import (
    SessionTeacherPreacherAssignmentRepository,
)


def _create_tenant(connection, tenant_id):
    connection.execute(
        """
        INSERT INTO tenants (tenant_id)
        VALUES (?)
        """,
        (tenant_id,),
    )
    connection.commit()


def _create_teacher_preacher(connection, tenant_id, name="Teacher One"):
    person = PersonRepository(connection).create(
        Person(id=None, name=name)
    )
    return TeacherPreacherRepository(connection).create(
        TeacherPreacher(
            id=None,
            tenant_id=tenant_id,
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )


def _create_session(connection, tenant_id, name="Teaching Session"):
    return TeachingSessionRepository(connection).create(
        TeachingSession(
            id=None,
            tenant_id=tenant_id,
            name=name,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
    )


def test_session_teacher_preacher_assignment_repository_create_get_list(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    session = _create_session(
        connection,
        "tenant-001",
    )

    repository = SessionTeacherPreacherAssignmentRepository(connection)

    assignment = SessionTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-001",
        teacher_preacher_id=teacher_preacher.id,
        teaching_session_id=session.id,
    )

    created = repository.create(assignment)

    assert created.id is not None
    assert created.tenant_id == "tenant-001"
    assert created.teacher_preacher_id == teacher_preacher.id
    assert created.teaching_session_id == session.id
    assert created.status == "active"

    fetched = repository.get("tenant-001", created.id)
    assert fetched == created

    assignments = repository.list("tenant-001")
    assert assignments == [created]


def test_session_teacher_preacher_assignment_repository_tenant_isolation(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    session = _create_session(
        connection,
        "tenant-001",
    )

    repository = SessionTeacherPreacherAssignmentRepository(connection)

    created = repository.create(
        SessionTeacherPreacherAssignment(
            id=None,
            tenant_id="tenant-001",
            teacher_preacher_id=teacher_preacher.id,
            teaching_session_id=session.id,
        )
    )

    assert repository.get("tenant-002", created.id) is None
    assert repository.list("tenant-002") == []


def test_duplicate_session_teacher_preacher_assignment_is_rejected(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    session = _create_session(
        connection,
        "tenant-001",
    )

    repository = SessionTeacherPreacherAssignmentRepository(connection)

    assignment = SessionTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-001",
        teacher_preacher_id=teacher_preacher.id,
        teaching_session_id=session.id,
    )

    repository.create(assignment)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(assignment)


def test_cross_tenant_teacher_preacher_reference_is_rejected(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    session = _create_session(
        connection,
        "tenant-002",
    )

    repository = SessionTeacherPreacherAssignmentRepository(connection)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            SessionTeacherPreacherAssignment(
                id=None,
                tenant_id="tenant-002",
                teacher_preacher_id=teacher_preacher.id,
                teaching_session_id=session.id,
            )
        )
