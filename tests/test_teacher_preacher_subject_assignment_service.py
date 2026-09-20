import sqlite3

import pytest

from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from models.teacher_preacher_subject_assignment import (
    TeacherPreacherSubjectAssignment,
)
from models.teaching_subject import TeachingSubject
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from repositories.teacher_preacher_subject_assignment_repository import (
    TeacherPreacherSubjectAssignmentRepository,
)
from repositories.teaching_subject_repository import TeachingSubjectRepository
from services.teacher_preacher_subject_assignment_service import (
    TeacherPreacherSubjectAssignmentService,
)


def _create_tenant(db_connection, tenant_id):
    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    db_connection.commit()


def _create_person(db_connection, tenant_id, name):
    cursor = db_connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (name,),
    )
    db_connection.commit()
    return cursor.lastrowid


def _create_teacher_preacher(db_connection, tenant_id, person_id):
    return TeacherPreacherRepository(db_connection).create(
        TeacherPreacher(
            id=None,
            tenant_id=tenant_id,
            person_id=person_id,
            role=TeacherPreacherRole.TEACHER,
        )
    )


def _create_subject(db_connection, tenant_id):
    return TeachingSubjectRepository(db_connection).create(
        TeachingSubject(
            id=None,
            tenant_id=tenant_id,
            name="Bible Study",
            status="active",
        )
    )


def test_create_get_list_round_trip(db_connection):
    tenant_id = "tenant-001"
    _create_tenant(db_connection, tenant_id)

    person_id = _create_person(db_connection, tenant_id, "Teacher One")
    capacity = _create_teacher_preacher(
        db_connection, tenant_id, person_id
    )
    subject = _create_subject(db_connection, tenant_id)

    repository = TeacherPreacherSubjectAssignmentRepository(db_connection)
    service = TeacherPreacherSubjectAssignmentService(
        repository,
        tenant_id,
    )

    created = service.create(
        TeacherPreacherSubjectAssignment(
            id=None,
            tenant_id=tenant_id,
            teacher_preacher_id=capacity.id,
            teaching_subject_id=subject.id,
        )
    )

    assert created.id is not None
    assert created.tenant_id == tenant_id
    assert created.teacher_preacher_id == capacity.id
    assert created.teaching_subject_id == subject.id
    assert created.status == "active"

    fetched = service.get(created.id)
    assert fetched == created

    listed = service.list()
    assert listed == [created]


def test_cross_tenant_create_rejected(db_connection):
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    _create_tenant(db_connection, tenant_a)
    _create_tenant(db_connection, tenant_b)

    person_id = _create_person(db_connection, tenant_a, "Teacher A")
    capacity = _create_teacher_preacher(
        db_connection, tenant_a, person_id
    )
    subject = _create_subject(db_connection, tenant_a)

    repository = TeacherPreacherSubjectAssignmentRepository(db_connection)
    service = TeacherPreacherSubjectAssignmentService(
        repository,
        tenant_b,
    )

    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id=tenant_a,
        teacher_preacher_id=capacity.id,
        teaching_subject_id=subject.id,
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(assignment)


def test_missing_write_permission_rejected(db_connection):
    tenant_id = "tenant-001"
    _create_tenant(db_connection, tenant_id)

    person_id = _create_person(db_connection, tenant_id, "Teacher One")
    capacity = _create_teacher_preacher(
        db_connection, tenant_id, person_id
    )
    subject = _create_subject(db_connection, tenant_id)

    repository = TeacherPreacherSubjectAssignmentRepository(db_connection)
    service = TeacherPreacherSubjectAssignmentService(
        repository,
        tenant_id,
        connection=db_connection,
        user_id="user-without-permission",
    )

    assignment = TeacherPreacherSubjectAssignment(
        id=None,
        tenant_id=tenant_id,
        teacher_preacher_id=capacity.id,
        teaching_subject_id=subject.id,
    )

    with pytest.raises(
        PermissionError,
        match="teacher_preacher_subject_assignment.write",
    ):
        service.create(assignment)


def test_missing_read_permission_rejected(db_connection):
    tenant_id = "tenant-001"
    _create_tenant(db_connection, tenant_id)

    repository = TeacherPreacherSubjectAssignmentRepository(db_connection)
    service = TeacherPreacherSubjectAssignmentService(
        repository,
        tenant_id,
        connection=db_connection,
        user_id="user-without-permission",
    )

    with pytest.raises(
        PermissionError,
        match="teacher_preacher_subject_assignment.read",
    ):
        service.list()


def test_get_is_tenant_bound(db_connection):
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    _create_tenant(db_connection, tenant_a)
    _create_tenant(db_connection, tenant_b)

    person_id = _create_person(db_connection, tenant_a, "Teacher A")
    capacity = _create_teacher_preacher(
        db_connection, tenant_a, person_id
    )
    subject = _create_subject(db_connection, tenant_a)

    repository = TeacherPreacherSubjectAssignmentRepository(db_connection)

    assignment = repository.create(
        TeacherPreacherSubjectAssignment(
            id=None,
            tenant_id=tenant_a,
            teacher_preacher_id=capacity.id,
            teaching_subject_id=subject.id,
        )
    )

    tenant_b_service = TeacherPreacherSubjectAssignmentService(
        repository,
        tenant_b,
    )

    assert tenant_b_service.get(assignment.id) is None
    assert tenant_b_service.list() == []
