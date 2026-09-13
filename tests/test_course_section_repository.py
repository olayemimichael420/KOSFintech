import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_subject import AcademicSubject
from models.academic_term import AcademicTerm
from models.course_offering import CourseOffering
from models.course_section import CourseSection
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.course_offering_repository import CourseOfferingRepository
from repositories.course_section_repository import CourseSectionRepository


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
        (tenant_id, "Course Section Test School", "secondary", "Nigeria", "NGN"),
    )
    connection.commit()

    class_repo = AcademicClassRepository(connection)
    subject_repo = AcademicSubjectRepository(connection)
    session_repo = AcademicSessionRepository(connection)
    term_repo = AcademicTermRepository(connection)
    offering_repo = CourseOfferingRepository(connection)

    academic_class = class_repo.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_id,
            name="Section Class",
        )
    )

    subject = subject_repo.create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_id,
            name="Section Subject",
        )
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

    return tenant_id, offering


def test_create_and_get(connection, academic_context):
    tenant_id, offering = academic_context
    repository = CourseSectionRepository(connection)

    section = repository.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )

    result = repository.get(tenant_id, section.id)

    assert result == section


def test_get_is_tenant_scoped(connection, academic_context):
    tenant_id, offering = academic_context
    repository = CourseSectionRepository(connection)

    section = repository.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )

    assert repository.get(str(uuid.uuid4()), section.id) is None


def test_list_is_tenant_and_offering_scoped(connection, academic_context):
    tenant_id, offering = academic_context
    repository = CourseSectionRepository(connection)

    repository.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )
    repository.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section B",
        )
    )

    result = repository.list(tenant_id, offering.id)

    assert [section.name for section in result] == [
        "Section A",
        "Section B",
    ]


def test_duplicate_section_name_rejected(connection, academic_context):
    tenant_id, offering = academic_context
    repository = CourseSectionRepository(connection)

    repository.create(
        CourseSection(
            id=None,
            tenant_id=tenant_id,
            course_offering_id=offering.id,
            name="Section A",
        )
    )

    with pytest.raises(Exception):
        repository.create(
            CourseSection(
                id=None,
                tenant_id=tenant_id,
                course_offering_id=offering.id,
                name="Section A",
            )
        )
