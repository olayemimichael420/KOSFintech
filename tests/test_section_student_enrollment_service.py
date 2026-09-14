import uuid

import pytest

from database import get_connection, init_db
from models.section_student_enrollment import SectionStudentEnrollment
from repositories.section_student_enrollment_repository import (
    SectionStudentEnrollmentRepository,
)
from services.section_student_enrollment_service import (
    SectionStudentEnrollmentService,
)


@pytest.fixture
def connection():
    init_db()
    connection = get_connection()
    yield connection
    connection.close()


class FakeRepository:
    def __init__(self):
        self.created = None

    def create(self, enrollment):
        self.created = enrollment
        return enrollment

    def get(self, tenant_id, enrollment_id):
        return None

    def list(self, tenant_id, course_section_id):
        return []


def test_create_rejects_tenant_mismatch(connection):
    tenant_id = str(uuid.uuid4())
    repository = FakeRepository()

    service = SectionStudentEnrollmentService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
    )

    enrollment = SectionStudentEnrollment(
        id=None,
        tenant_id=str(uuid.uuid4()),
        course_section_id=1,
        student_id=1,
    )

    with pytest.raises(
        ValueError,
        match="section student enrollment tenant mismatch",
    ):
        service.create(enrollment)


def test_create_delegates_to_repository(connection):
    tenant_id = str(uuid.uuid4())
    repository = FakeRepository()

    service = SectionStudentEnrollmentService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
    )

    enrollment = SectionStudentEnrollment(
        id=None,
        tenant_id=tenant_id,
        course_section_id=1,
        student_id=1,
    )

    result = service.create(enrollment)

    assert result is enrollment
    assert repository.created is enrollment


def test_get_and_list_are_tenant_scoped(connection):
    tenant_id = str(uuid.uuid4())

    class TrackingRepository:
        def get(self, tenant_id_arg, enrollment_id):
            self.get_args = (tenant_id_arg, enrollment_id)
            return None

        def list(self, tenant_id_arg, course_section_id):
            self.list_args = (tenant_id_arg, course_section_id)
            return []

    repository = TrackingRepository()

    service = SectionStudentEnrollmentService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
    )

    assert service.get(7) is None
    assert repository.get_args == (tenant_id, 7)

    assert service.list(11) == []
    assert repository.list_args == (tenant_id, 11)
