import sqlite3
import uuid

import pytest

from database import get_connection, init_db
from models.student import Student
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from models.student_enrollment import StudentEnrollment
from repositories.student_repository import StudentRepository
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.student_enrollment_repository import StudentEnrollmentRepository


@pytest.fixture
def setup():
    init_db()
    connection = get_connection()
    try:

        tenant_suffix = uuid.uuid4().hex
        tenant_a = f"enrollment-a-{tenant_suffix}"
        tenant_b = f"enrollment-b-{tenant_suffix}"

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

        repository = StudentEnrollmentRepository(connection)

        yield (
            connection,
            repository,
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


def test_create_and_get(setup):
    (
        _,
        repository,
        tenant_a,
        _,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment = repository.create(
        make_enrollment(
            tenant_a,
            students,
            classes,
            sessions,
            terms,
        )
    )

    loaded = repository.get(tenant_a, enrollment.id)

    assert loaded is not None
    assert loaded.id == enrollment.id
    assert loaded.tenant_id == tenant_a
    assert loaded.student_id == students[tenant_a].id
    assert loaded.academic_class_id == classes[tenant_a].id
    assert loaded.academic_session_id == sessions[tenant_a].id
    assert loaded.academic_term_id == terms[tenant_a].id


def test_get_is_tenant_scoped(setup):
    (
        _,
        repository,
        tenant_a,
        tenant_b,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment = repository.create(
        make_enrollment(
            tenant_a,
            students,
            classes,
            sessions,
            terms,
        )
    )

    assert repository.get(tenant_b, enrollment.id) is None


def test_list_is_tenant_and_student_scoped(setup):
    (
        _,
        repository,
        tenant_a,
        tenant_b,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    enrollment_a = repository.create(
        make_enrollment(
            tenant_a,
            students,
            classes,
            sessions,
            terms,
        )
    )

    enrollment_b = repository.create(
        make_enrollment(
            tenant_b,
            students,
            classes,
            sessions,
            terms,
        )
    )

    result_a = repository.list(
        tenant_a,
        students[tenant_a].id,
    )
    result_b = repository.list(
        tenant_b,
        students[tenant_b].id,
    )

    assert [item.id for item in result_a] == [enrollment_a.id]
    assert [item.id for item in result_b] == [enrollment_b.id]


def test_active_term_enrollment_is_unique(setup):
    (
        _,
        repository,
        tenant_a,
        _,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    first = make_enrollment(
        tenant_a,
        students,
        classes,
        sessions,
        terms,
    )

    repository.create(first)

    duplicate = make_enrollment(
        tenant_a,
        students,
        classes,
        sessions,
        terms,
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(duplicate)


def test_active_session_enrollment_is_unique(setup):
    (
        connection,
        repository,
        tenant_a,
        _,
        students,
        classes,
        sessions,
        _,
    ) = setup

    first = StudentEnrollment(
        id=None,
        tenant_id=tenant_a,
        student_id=students[tenant_a].id,
        academic_class_id=classes[tenant_a].id,
        academic_session_id=sessions[tenant_a].id,
        academic_term_id=None,
        enrollment_date="2026-09-01",
    )

    repository.create(first)

    duplicate = StudentEnrollment(
        id=None,
        tenant_id=tenant_a,
        student_id=students[tenant_a].id,
        academic_class_id=classes[tenant_a].id,
        academic_session_id=sessions[tenant_a].id,
        academic_term_id=None,
        enrollment_date="2026-10-01",
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(duplicate)


def test_inactive_enrollments_can_repeat(setup):
    (
        _,
        repository,
        tenant_a,
        _,
        students,
        classes,
        sessions,
        terms,
    ) = setup

    first = make_enrollment(
        tenant_a,
        students,
        classes,
        sessions,
        terms,
    )
    first.status = "inactive"
    repository.create(first)

    second = make_enrollment(
        tenant_a,
        students,
        classes,
        sessions,
        terms,
    )
    second.status = "inactive"
    repository.create(second)

    assert len(repository.list(tenant_a, students[tenant_a].id)) == 2
