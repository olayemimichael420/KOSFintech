import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_subject import AcademicSubject
from models.academic_term import AcademicTerm
from models.course_offering import CourseOffering
from models.course_section import CourseSection
from models.section_teacher_assignment import SectionTeacherAssignment
from models.teacher import Teacher
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.course_offering_repository import CourseOfferingRepository
from repositories.course_section_repository import CourseSectionRepository
from repositories.section_teacher_assignment_repository import (
    SectionTeacherAssignmentRepository,
)
from repositories.teacher_repository import TeacherRepository
from services.section_teacher_assignment_service import (
    SectionTeacherAssignmentService,
)


@pytest.fixture
def connection():
    init_db()
    connection = get_connection()
    yield connection
    connection.close()


@pytest.fixture
def service_context(connection):
    tenant_id = str(uuid.uuid4())

    connection.execute(
        """
        INSERT INTO schools (tenant_id, name, school_type, country, currency)
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_id, "Section Teacher Service School", "secondary", "Nigeria", "NGN"),
    )
    connection.commit()

    academic_class = AcademicClassRepository(connection).create(
        AcademicClass(id=None, tenant_id=tenant_id, name="Test Class")
    )
    subject = AcademicSubjectRepository(connection).create(
        AcademicSubject(id=None, tenant_id=tenant_id, name="Test Subject")
    )
    session = AcademicSessionRepository(connection).create(
        AcademicSession(
            id=None,
            tenant_id=tenant_id,
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )
    term = AcademicTermRepository(connection).create(
        AcademicTerm(
            id=None,
            tenant_id=tenant_id,
            academic_session_id=session.id,
            name="Term 1",
            start_date="2026-09-01",
            end_date="2026-12-18",
        )
    )
    offering = CourseOfferingRepository(connection).create(
        CourseOffering(
            id=None,
            tenant_id=tenant_id,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )
    section = CourseSectionRepository(connection).create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )
    teacher = TeacherRepository(connection).create(
        Teacher(
            id=None,
            tenant_id=tenant_id,
            user_id=None,
            name="Teacher A",
            subject="Test Subject",
            qualification=None,
        )
    )

    repository = SectionTeacherAssignmentRepository(connection)
    service = SectionTeacherAssignmentService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
    )

    return tenant_id, section, teacher, service


def test_create_and_get(service_context):
    tenant_id, section, teacher, service = service_context

    assignment = service.create(
        SectionTeacherAssignment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section.id,
            teacher_id=teacher.id,
        )
    )

    found = service.get(assignment.id)

    assert found == assignment


def test_list_is_tenant_and_section_scoped(service_context):
    tenant_id, section, teacher, service = service_context

    assignment = service.create(
        SectionTeacherAssignment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section.id,
            teacher_id=teacher.id,
        )
    )

    result = service.list(section.id)

    assert len(result) == 1
    assert result[0] == assignment


def test_create_rejects_tenant_mismatch(service_context):
    _, section, teacher, service = service_context

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(
            SectionTeacherAssignment(
                id=None,
                tenant_id=str(uuid.uuid4()),
                course_section_id=section.id,
                teacher_id=teacher.id,
            )
        )
