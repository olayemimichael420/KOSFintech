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


@pytest.fixture
def repository_context():
    init_db()
    connection = get_connection()

    suffix = uuid.uuid4().hex
    tenant_a = f"course-offering-a-{suffix}"
    tenant_b = f"course-offering-b-{suffix}"

    try:
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_a, "School A", "secondary", "NG", "NGN"),
        )
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id, name, school_type, country, currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_b, "School B", "secondary", "NG", "NGN"),
        )
        connection.commit()

        class_repo = AcademicClassRepository(connection)
        subject_repo = AcademicSubjectRepository(connection)
        session_repo = AcademicSessionRepository(connection)
        term_repo = AcademicTermRepository(connection)

        academic_class = class_repo.create(
            AcademicClass(
                id=None,
                tenant_id=tenant_a,
                name="JSS 1",
            )
        )

        subject = subject_repo.create(
            AcademicSubject(
                id=None,
                tenant_id=tenant_a,
                name="Mathematics",
            )
        )

        session = session_repo.create(
            AcademicSession(
                id=None,
                tenant_id=tenant_a,
                name="2026/2027",
                start_date="2026-09-01",
                end_date="2027-07-31",
            )
        )

        term = term_repo.create(
            AcademicTerm(
                id=None,
                tenant_id=tenant_a,
                academic_session_id=session.id,
                name="First Term",
                start_date="2026-09-01",
                end_date="2026-12-18",
            )
        )

        yield (
            connection,
            tenant_a,
            tenant_b,
            academic_class,
            subject,
            session,
            term,
        )
    finally:
        connection.close()


def test_create_and_get_course_offering(repository_context):
    (
        connection,
        tenant_a,
        _tenant_b,
        academic_class,
        subject,
        session,
        term,
    ) = repository_context

    repository = CourseOfferingRepository(connection)

    offering = repository.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_a,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    result = repository.get(tenant_a, offering.id)

    assert result == offering


def test_get_is_tenant_scoped(repository_context):
    (
        connection,
        tenant_a,
        tenant_b,
        academic_class,
        subject,
        session,
        term,
    ) = repository_context

    repository = CourseOfferingRepository(connection)

    offering = repository.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_a,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    assert repository.get(tenant_b, offering.id) is None


def test_list_is_tenant_scoped(repository_context):
    (
        connection,
        tenant_a,
        tenant_b,
        academic_class,
        subject,
        session,
        term,
    ) = repository_context

    repository = CourseOfferingRepository(connection)

    offering = repository.create(
        CourseOffering(
            id=None,
            tenant_id=tenant_a,
            academic_class_id=academic_class.id,
            academic_subject_id=subject.id,
            academic_session_id=session.id,
            academic_term_id=term.id,
        )
    )

    assert repository.list(tenant_a) == [offering]
    assert repository.list(tenant_b) == []


def test_duplicate_course_offering_is_rejected(repository_context):
    (
        connection,
        tenant_a,
        _tenant_b,
        academic_class,
        subject,
        session,
        term,
    ) = repository_context

    repository = CourseOfferingRepository(connection)

    offering = CourseOffering(
        id=None,
        tenant_id=tenant_a,
        academic_class_id=academic_class.id,
        academic_subject_id=subject.id,
        academic_session_id=session.id,
        academic_term_id=term.id,
    )

    repository.create(offering)

    with pytest.raises(Exception):
        repository.create(offering)
