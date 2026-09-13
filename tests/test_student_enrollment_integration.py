import sqlite3
import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from models.student import Student
from models.student_enrollment import StudentEnrollment
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.student_repository import StudentRepository
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


@pytest.fixture
def setup():
    init_db()
    connection = get_connection()
    try:

        tenant_suffix = uuid.uuid4().hex
        tenant_a = f"enrollment-integration-a-{tenant_suffix}"
        tenant_b = f"enrollment-integration-b-{tenant_suffix}"

        for tenant_id in (tenant_a, tenant_b):
            connection.execute(
                """
                INSERT INTO schools (
                    tenant_id, name, school_type, country, currency
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, tenant_id, "secondary", "NG", "NGN"),
            )

        student_repo = StudentRepository(connection)
        class_repo = AcademicClassRepository(connection)
        session_repo = AcademicSessionRepository(connection)
        term_repo = AcademicTermRepository(connection)

        students = {}
        classes = {}
        sessions = {}
        terms = {}

        for tenant_id in (tenant_a, tenant_b):
            students[tenant_id] = student_repo.create(
                Student(
                    id=None,
                    tenant_id=tenant_id,
                    user_id=None,
                    name=f"Student {tenant_id}",
                    class_name="JSS 1",
                    age=12,
                    guardian_id=None,
                    enrollment_date="2026-09-01",
                )
            )

            classes[tenant_id] = class_repo.create(
                AcademicClass(
                    id=None,
                    tenant_id=tenant_id,
                    name="JSS 1",
                    education_level="secondary",
                    sequence=1,
                )
            )

            sessions[tenant_id] = session_repo.create(
                AcademicSession(
                    id=None,
                    tenant_id=tenant_id,
                    name="2026/2027",
                    start_date="2026-09-01",
                    end_date="2027-07-31",
                )
            )

            terms[tenant_id] = term_repo.create(
                AcademicTerm(
                    id=None,
                    tenant_id=tenant_id,
                    academic_session_id=sessions[tenant_id].id,
                    name="Term 1",
                    start_date="2026-09-01",
                    end_date="2026-12-18",
                )
            )

        factory = ApplicationServiceFactory(connection)
        services = ApplicationServices(factory)

        yield (
            connection,
            services,
            tenant_a,
            tenant_b,
            students,
            classes,
            sessions,
            terms,
        )

    finally:
        connection.close()


def make_enrollment(tenant_id, students, classes, sessions, terms):
    return StudentEnrollment(
        id=None,
        tenant_id=tenant_id,
        student_id=students[tenant_id].id,
        academic_class_id=classes[tenant_id].id,
        academic_session_id=sessions[tenant_id].id,
        academic_term_id=terms[tenant_id].id,
        enrollment_date="2026-09-01",
    )


def test_end_to_end_enrollment_lifecycle(setup):
    (
        _,
        services,
        tenant_a,
        tenant_b,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment_service = services.student_enrollment(tenant_a)

    enrollment = enrollment_service.create(
        make_enrollment(
            tenant_a,
            students,
            classes,
            sessions,
            terms,
        )
    )

    assert enrollment.id is not None
    assert enrollment.tenant_id == tenant_a

    loaded = enrollment_service.get(enrollment.id)

    assert loaded is not None
    assert loaded.id == enrollment.id
    assert loaded.student_id == students[tenant_a].id
    assert loaded.academic_class_id == classes[tenant_a].id
    assert loaded.academic_session_id == sessions[tenant_a].id
    assert loaded.academic_term_id == terms[tenant_a].id

    listed = enrollment_service.list(students[tenant_a].id)

    assert len(listed) == 1
    assert listed[0].id == enrollment.id

    other_tenant_service = services.student_enrollment(tenant_b)

    assert other_tenant_service.get(enrollment.id) is None
    assert other_tenant_service.list(students[tenant_a].id) == []


def test_end_to_end_duplicate_active_term_enrollment_is_rejected(setup):
    (
        _,
        services,
        tenant_a,
        _,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment_service = services.student_enrollment(tenant_a)

    enrollment_service.create(
        make_enrollment(
            tenant_a,
            students,
            classes,
            sessions,
            terms,
        )
    )

    duplicate = make_enrollment(
        tenant_a,
        students,
        classes,
        sessions,
        terms,
    )

    with pytest.raises(sqlite3.IntegrityError):
        enrollment_service.create(duplicate)


def test_end_to_end_tenant_mismatch_is_rejected(setup):
    (
        _,
        services,
        tenant_a,
        tenant_b,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment_service = services.student_enrollment(tenant_a)

    enrollment = make_enrollment(
        tenant_b,
        students,
        classes,
        sessions,
        terms,
    )

    with pytest.raises(ValueError, match="student enrollment tenant mismatch"):
        enrollment_service.create(enrollment)
