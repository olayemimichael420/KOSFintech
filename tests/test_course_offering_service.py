import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_subject import AcademicSubject
from models.academic_term import AcademicTerm
from models.course_offering import CourseOffering
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.course_offering_repository import CourseOfferingRepository
from services.course_offering_service import CourseOfferingService


@pytest.fixture
def service_context():
    init_db()
    connection = get_connection()

    suffix = uuid.uuid4().hex
    tenant_id = f"course-offering-service-{suffix}"

    try:
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_id, "Course Offering School", "secondary", "NG", "NGN"),
        )
        connection.commit()

        class_repo = AcademicClassRepository(connection)
        subject_repo = AcademicSubjectRepository(connection)
        session_repo = AcademicSessionRepository(connection)
        term_repo = AcademicTermRepository(connection)

        academic_class = class_repo.create(
            AcademicClass(
                id=None,
                tenant_id=tenant_id,
                name="JSS 1",
            )
        )

        subject = subject_repo.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_id,
                name="Mathematics",
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
                name="First Term",
                start_date="2026-09-01",
                end_date="2026-12-18",
            )
        )

        repository = CourseOfferingRepository(connection)
        service = CourseOfferingService(
            repository=repository,
            tenant_id=tenant_id,
            connection=connection,
        )

        yield connection, tenant_id, academic_class, subject, session, term, service
    finally:
        connection.close()


def test_create_and_get_course_offering(service_context):
    (
        _connection,
        tenant_id,
        academic_class,
        subject,
        session,
        term,
        service,
    ) = service_context

    offering = service.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_id,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    assert service.get(offering.id) == offering


def test_create_rejects_tenant_mismatch(service_context):
    (
        _connection,
        _tenant_id,
        academic_class,
        subject,
        session,
        term,
        service,
    ) = service_context

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(
            CourseOffering(
                id=None,
                tenant_id="wrong-tenant",
                academic_class_id=academic_class.id,
                academic_subject_id=subject.id,
                academic_session_id=session.id,
                academic_term_id=term.id,
            )
        )


def test_list_is_tenant_scoped(service_context):
    (
        _connection,
        tenant_id,
        academic_class,
        subject,
        session,
        term,
        service,
    ) = service_context

    offering = service.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_id,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    assert service.list() == [offering]


def test_read_requires_permission_when_user_is_present(service_context):
    (
        connection,
        tenant_id,
        _academic_class,
        _subject,
        _session,
        _term,
        _service,
    ) = service_context

    repository = CourseOfferingRepository(connection)
    service = CourseOfferingService(
        repository=repository,
        tenant_id=tenant_id,
        connection=connection,
        user_id=999999,
    )

    with pytest.raises(PermissionError, match="course_offering.read"):
        service.list()
