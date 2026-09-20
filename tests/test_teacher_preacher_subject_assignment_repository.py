import sqlite3

import pytest

from models.person import Person
from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from models.teaching_subject import TeachingSubject
from models.teacher_preacher_subject_assignment import (
    TeacherPreacherSubjectAssignment,
)
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from repositories.teaching_subject_repository import TeachingSubjectRepository
from repositories.teacher_preacher_subject_assignment_repository import (
    TeacherPreacherSubjectAssignmentRepository,
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


def _create_subject(connection, tenant_id, name="Faith"):
    return TeachingSubjectRepository(connection).create(
        TeachingSubject(
            id=None,
            tenant_id=tenant_id,
            name=name,
        )
    )


def test_teacher_preacher_subject_assignment_repository_create_get_list(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    subject = _create_subject(
        connection,
        "tenant-001",
    )

    repository = TeacherPreacherSubjectAssignmentRepository(connection)

    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id="tenant-001",
        teacher_preacher_id=teacher_preacher.id,
        teaching_subject_id=subject.id,
    )

    created = repository.create(assignment)

    assert created.id is not None
    assert created.tenant_id == "tenant-001"
    assert created.teacher_preacher_id == teacher_preacher.id
    assert created.teaching_subject_id == subject.id
    assert created.status == "active"

    fetched = repository.get("tenant-001", created.id)

    assert fetched == created

    assignments = repository.list("tenant-001")

    assert assignments == [created]


def test_teacher_preacher_subject_assignment_repository_tenant_isolation(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    subject = _create_subject(
        connection,
        "tenant-001",
    )

    repository = TeacherPreacherSubjectAssignmentRepository(connection)

    created = repository.create(
        TeacherPreacherSubjectAssignment(
            id=None,
            tenant_id="tenant-001",
            teacher_preacher_id=teacher_preacher.id,
            teaching_subject_id=subject.id,
        )
    )

    assert repository.get("tenant-002", created.id) is None
    assert repository.list("tenant-002") == []


def test_duplicate_teacher_preacher_subject_assignment_is_rejected(
    db_connection,
):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    teacher_preacher = _create_teacher_preacher(
        connection,
        "tenant-001",
    )
    subject = _create_subject(
        connection,
        "tenant-001",
    )

    repository = TeacherPreacherSubjectAssignmentRepository(connection)

    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id="tenant-001",
        teacher_preacher_id=teacher_preacher.id,
        teaching_subject_id=subject.id,
    )

    repository.create(assignment)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(assignment)
