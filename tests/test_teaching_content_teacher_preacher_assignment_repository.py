import sqlite3

import pytest

from models.teaching_session import TeachingSession
from repositories.teaching_session_repository import TeachingSessionRepository
from models.teaching_series import TeachingSeries
from repositories.teaching_series_repository import TeachingSeriesRepository
from models.person import Person
from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from models.teaching_content import TeachingContent
from models.teaching_focus import TeachingFocus
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from repositories.teaching_content_repository import TeachingContentRepository
from repositories.teaching_focus_repository import TeachingFocusRepository
from repositories.teaching_content_teacher_preacher_assignment_repository import (
    TeachingContentTeacherPreacherAssignmentRepository,
)
from models.teaching_content_teacher_preacher_assignment import (
    TeachingContentTeacherPreacherAssignment,
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


def _create_content(connection, tenant_id, name="Introduction"):
    session = TeachingSessionRepository(connection).create(
        TeachingSession(
            id=None,
            tenant_id=tenant_id,
            name="2026 Teaching Session",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    series = TeachingSeriesRepository(connection).create(
        TeachingSeries(
            id=None,
            tenant_id=tenant_id,
            teaching_session_id=session.id,
            name="Faith Series",
            start_date="2026-01-10",
            end_date="2026-02-10",
        )
    )

    focus = TeachingFocusRepository(connection).create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_id,
            teaching_series_id=series.id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    return TeachingContentRepository(connection).create(
        TeachingContent(
            id=None,
            tenant_id=tenant_id,
            teaching_focus_id=focus.id,
            name=name,
        )
    )


def test_repository_create_get_list_round_trip(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    content = _create_content(
        connection,
        "tenant-001",
    )

    repository = TeachingContentTeacherPreacherAssignmentRepository(
        connection
    )

    assignment = TeachingContentTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-001",
        teaching_content_id=content.id,
        teacher_preacher_id=teacher_preacher.id,
    )

    created = repository.create(assignment)

    assert created.id is not None
    assert created.tenant_id == "tenant-001"
    assert created.teaching_content_id == content.id
    assert created.teacher_preacher_id == teacher_preacher.id
    assert created.status == "active"

    fetched = repository.get("tenant-001", created.id)

    assert fetched == created

    assignments = repository.list(
        "tenant-001",
        content.id,
    )

    assert assignments == [created]


def test_repository_tenant_isolation(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    content = _create_content(
        connection,
        "tenant-001",
    )

    repository = TeachingContentTeacherPreacherAssignmentRepository(
        connection
    )

    created = repository.create(
        TeachingContentTeacherPreacherAssignment(
            id=None,
            tenant_id="tenant-001",
            teaching_content_id=content.id,
            teacher_preacher_id=teacher_preacher.id,
        )
    )

    assert repository.get("tenant-002", created.id) is None
    assert repository.list("tenant-002", content.id) == []


def test_duplicate_assignment_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    content = _create_content(
        connection,
        "tenant-001",
    )

    repository = TeachingContentTeacherPreacherAssignmentRepository(
        connection
    )

    assignment = TeachingContentTeacherPreacherAssignment(
        id=None,
        tenant_id="tenant-001",
        teaching_content_id=content.id,
        teacher_preacher_id=teacher_preacher.id,
    )

    repository.create(assignment)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(assignment)


def test_cross_tenant_content_reference_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    content = _create_content(
        connection,
        "tenant-002",
    )

    repository = TeachingContentTeacherPreacherAssignmentRepository(
        connection
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            TeachingContentTeacherPreacherAssignment(
                id=None,
                tenant_id="tenant-001",
                teaching_content_id=content.id,
                teacher_preacher_id=teacher_preacher.id,
            )
        )


def test_cross_tenant_teacher_preacher_reference_is_rejected(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-002",
    )
    content = _create_content(
        connection,
        "tenant-001",
    )

    repository = TeachingContentTeacherPreacherAssignmentRepository(
        connection
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            TeachingContentTeacherPreacherAssignment(
                id=None,
                tenant_id="tenant-001",
                teaching_content_id=content.id,
                teacher_preacher_id=teacher_preacher.id,
            )
        )
