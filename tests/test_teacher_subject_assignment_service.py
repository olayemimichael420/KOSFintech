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
from services.teacher_subject_assignment_service import (
    TeacherSubjectAssignmentService,
)


@pytest.fixture
def setup():
    init_db()
    connection = get_connection()

    tenant_id = f"assignment-service-{uuid.uuid4().hex}"

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

    teacher = TeacherRepository(connection).create(
        Teacher(
            id=None,
            tenant_id=tenant_id,
            user_id=None,
            name="Teacher A",
            subject="Mathematics",
            qualification=None,
        )
    )

    subject = AcademicSubjectRepository(connection).create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_id,
            name="Mathematics",
        )
    )

    repository = TeacherSubjectAssignmentRepository(connection)
    service = TeacherSubjectAssignmentService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
    )

    yield connection, tenant_id, teacher, subject, service
    connection.close()


def test_create_and_get(setup):
    _, tenant_id, teacher, subject, service = setup

    assignment = service.create(
        TeacherSubjectAssignment(
            id=None,
            tenant_id=tenant_id,
            teacher_id=teacher.id,
            academic_subject_id=subject.id,
        )
    )

    found = service.get(assignment.id)

    assert found is not None
    assert found.teacher_id == teacher.id
    assert found.academic_subject_id == subject.id


def test_tenant_mismatch_rejected(setup):
    _, _, teacher, subject, service = setup

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(
            TeacherSubjectAssignment(
                id=None,
                tenant_id="different-tenant",
                teacher_id=teacher.id,
                academic_subject_id=subject.id,
            )
        )


def test_list_is_tenant_scoped(setup):
    _, tenant_id, teacher, subject, service = setup

    service.create(
        TeacherSubjectAssignment(
            id=None,
            tenant_id=tenant_id,
            teacher_id=teacher.id,
            academic_subject_id=subject.id,
        )
    )

    assignments = service.list()

    assert len(assignments) == 1
    assert assignments[0].tenant_id == tenant_id
