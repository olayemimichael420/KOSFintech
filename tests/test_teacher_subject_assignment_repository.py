import uuid

import pytest

from database import get_connection, init_db
from models.teacher import Teacher
from models.academic_subject import AcademicSubject
from models.teacher_subject_assignment import TeacherSubjectAssignment
from repositories.teacher_repository import TeacherRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.teacher_subject_assignment_repository import (
    TeacherSubjectAssignmentRepository,
)


@pytest.fixture
def setup():
    init_db()
    connection = get_connection()

    suffix = uuid.uuid4().hex
    tenant_a = f"assignment-a-{suffix}"
    tenant_b = f"assignment-b-{suffix}"

    for tenant_id in (tenant_a, tenant_b):
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                tenant_id,
                "secondary",
                "NG",
                "NGN",
            ),
        )

    connection.commit()

    teacher_repo = TeacherRepository(connection)
    subject_repo = AcademicSubjectRepository(connection)
    assignment_repo = TeacherSubjectAssignmentRepository(connection)

    teacher = teacher_repo.create(
        Teacher(
            id=None,
            tenant_id=tenant_a,
            user_id=None,
            name="Teacher A",
            subject="Mathematics",
            qualification=None,
        )
    )

    subject = subject_repo.create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_a,
            name="Mathematics",
        )
    )

    other_subject = subject_repo.create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_b,
            name="Mathematics",
        )
    )

    yield (
        connection,
        tenant_a,
        tenant_b,
        teacher,
        subject,
        other_subject,
        assignment_repo,
    )

    connection.close()


def test_create_and_get(setup):
    (
        _,
        tenant_a,
        _,
        teacher,
        subject,
        _,
        repository,
    ) = setup

    assignment = repository.create(
        TeacherSubjectAssignment(
            id=None,
            tenant_id=tenant_a,
            teacher_id=teacher.id,
            academic_subject_id=subject.id,
        )
    )

    found = repository.get(tenant_a, assignment.id)

    assert found is not None
    assert found.teacher_id == teacher.id
    assert found.academic_subject_id == subject.id


def test_get_is_tenant_scoped(setup):
    (
        _,
        tenant_a,
        tenant_b,
        teacher,
        subject,
        _,
        repository,
    ) = setup

    assignment = repository.create(
        TeacherSubjectAssignment(
            id=None,
            tenant_id=tenant_a,
            teacher_id=teacher.id,
            academic_subject_id=subject.id,
        )
    )

    assert repository.get(tenant_b, assignment.id) is None


def test_list_is_tenant_scoped(setup):
    (
        _,
        tenant_a,
        tenant_b,
        teacher,
        subject,
        _,
        repository,
    ) = setup

    repository.create(
        TeacherSubjectAssignment(
            id=None,
            tenant_id=tenant_a,
            teacher_id=teacher.id,
            academic_subject_id=subject.id,
        )
    )

    assert len(repository.list(tenant_a)) == 1
    assert repository.list(tenant_b) == []


def test_cross_tenant_subject_assignment_rejected(setup):
    (
        connection,
        tenant_a,
        _,
        teacher,
        _,
        other_subject,
        repository,
    ) = setup

    with pytest.raises(Exception):
        repository.create(
            TeacherSubjectAssignment(
                id=None,
                tenant_id=tenant_a,
                teacher_id=teacher.id,
                academic_subject_id=other_subject.id,
            )
        )

    connection.rollback()
