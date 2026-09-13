import uuid

import pytest

from database import get_connection, init_db
from models.teacher import Teacher
from models.academic_class import AcademicClass
from models.academic_subject import AcademicSubject
from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from models.course_offering import CourseOffering
from models.course_section import CourseSection
from models.section_teacher_assignment import SectionTeacherAssignment
from repositories.course_section_repository import CourseSectionRepository
from repositories.course_offering_repository import CourseOfferingRepository
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.teacher_repository import TeacherRepository
from repositories.section_teacher_assignment_repository import (
    SectionTeacherAssignmentRepository,
)


@pytest.fixture
def connection():
    init_db()
    connection = get_connection()
    yield connection
    connection.close()


@pytest.fixture
def academic_context(connection):
    tenant_id = str(uuid.uuid4())

    connection.execute(
        """
        INSERT INTO schools (tenant_id, name, school_type, country, currency)
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_id, "Section Teacher Test School", "secondary", "Nigeria", "NGN"),
    )
    connection.commit()

    class_repo = AcademicClassRepository(connection)
    subject_repo = AcademicSubjectRepository(connection)
    session_repo = AcademicSessionRepository(connection)
    term_repo = AcademicTermRepository(connection)
    offering_repo = CourseOfferingRepository(connection)
    section_repo = CourseSectionRepository(connection)
    teacher_repo = TeacherRepository(connection)

    academic_class = class_repo.create(
        AcademicClass(id=None, tenant_id=tenant_id, name="Test Class")
    )

    subject = subject_repo.create(
        AcademicSubject(id=None, tenant_id=tenant_id, name="Test Subject")
    )

    session = session_repo.create(
        AcademicSession(
            id=None,
            tenant_id=tenant_id,
            name="2026/2027",
            start_date="2026-09-01",
            end_date="2027-07-31",
        )
    )

    term = term_repo.create(
        AcademicTerm(
            id=None,
            tenant_id=tenant_id,
            academic_session_id=session.id,
            name="Term 1",
            start_date="2026-09-01",
            end_date="2026-12-18",
        )
    )

    offering = offering_repo.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_id,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    section = section_repo.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )

    teacher = teacher_repo.create(
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

    return tenant_id, section, teacher, repository


def test_create_and_get(connection, academic_context):
    tenant_id, section, teacher, repository = academic_context

    assignment = repository.create(
        SectionTeacherAssignment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section.id,
            teacher_id=teacher.id,
        )
    )

    found = repository.get(tenant_id, assignment.id)

    assert found == assignment


def test_get_is_tenant_scoped(academic_context):
    tenant_id, section, teacher, repository = academic_context

    assignment = repository.create(
        SectionTeacherAssignment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section.id,
            teacher_id=teacher.id,
        )
    )

    assert repository.get(str(uuid.uuid4()), assignment.id) is None


def test_list_is_section_scoped(academic_context):
    tenant_id, section, teacher, repository = academic_context

    repository.create(
        SectionTeacherAssignment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section.id,
            teacher_id=teacher.id,
        )
    )

    result = repository.list(tenant_id, section.id)

    assert len(result) == 1
    assert result[0].teacher_id == teacher.id


def test_cross_tenant_section_assignment_rejected(
    connection,
    academic_context,
):
    _, section, teacher, repository = academic_context
    other_tenant = str(uuid.uuid4())

    connection.execute(
        """
        INSERT INTO schools (tenant_id, name, school_type, country, currency)
        VALUES (?, ?, ?, ?, ?)
        """,
        (other_tenant, "Other School", "secondary", "Nigeria", "NGN"),
    )
    connection.commit()

    with pytest.raises(Exception):
        repository.create(
            SectionTeacherAssignment(
                id=None,
                tenant_id=other_tenant,
                course_section_id=section.id,
                teacher_id=teacher.id,
            )
        )

def test_duplicate_teacher_assignment_rejected(academic_context):
    tenant_id, section, teacher, repository = academic_context

    assignment = SectionTeacherAssignment(
        id=None,
        tenant_id=tenant_id,
        course_section_id=section.id,
        teacher_id=teacher.id,
    )

    repository.create(assignment)

    with pytest.raises(Exception):
        repository.create(
            SectionTeacherAssignment(
                id=None,
                tenant_id=tenant_id,
                course_section_id=section.id,
                teacher_id=teacher.id,
            )
        )
