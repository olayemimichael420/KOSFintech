import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.academic_subject import AcademicSubject
from models.academic_term import AcademicTerm
from models.course_offering import CourseOffering
from models.course_section import CourseSection
from models.school import School
from models.student import Student
from repositories.section_student_enrollment_repository import (
    SectionStudentEnrollmentRepository,
)
from models.section_student_enrollment import SectionStudentEnrollment


@pytest.fixture
def connection():
    init_db()
    connection = get_connection()
    yield connection
    connection.close()


def _school(connection, tenant_id):
    school = School(
        tenant_id=tenant_id,
        name=f"School {tenant_id}",
        school_type="secondary",
        country="NG",
        currency="NGN",
    )
    connection.execute(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            school.tenant_id,
            school.name,
            school.school_type,
            school.country,
            school.currency,
        ),
    )
    connection.commit()


def _student(connection, tenant_id):
    student = Student(
        id=None,
        tenant_id=tenant_id,
        user_id=None,
        name="Student One",
        class_name="Legacy",
        age=12,
        guardian_id=None,
        enrollment_date=None,
        status="active",
    )
    cursor = connection.execute(
        """
        INSERT INTO students (
            tenant_id, user_id, name, class_name,
            age, guardian_id, enrollment_date, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student.tenant_id,
            student.user_id,
            student.name,
            student.class_name,
            student.age,
            student.guardian_id,
            student.enrollment_date,
            student.status,
        ),
    )
    connection.commit()
    student.id = cursor.lastrowid
    return student


def _section(connection, tenant_id, class_name="Class A"):
    academic_class = AcademicClass(
        id=None,
        tenant_id=tenant_id,
        name=class_name,
    )
    connection.execute(
        """
        INSERT INTO academic_classes (
            tenant_id, name, education_level, sequence, status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            academic_class.tenant_id,
            academic_class.name,
            academic_class.education_level,
            academic_class.sequence,
            academic_class.status,
        ),
    )

    subject = AcademicSubject(
        id=None,
        tenant_id=tenant_id,
        name=f"Mathematics {class_name}",
    )
    connection.execute(
        """
        INSERT INTO academic_subjects (tenant_id, name, status)
        VALUES (?, ?, ?)
        """,
        (subject.tenant_id, subject.name, subject.status),
    )

    session = AcademicSession(
        id=None,
        tenant_id=tenant_id,
        name=f"2026/2027 {class_name}",
        start_date="2026-09-01",
        end_date="2027-07-31",
    )
    connection.execute(
        """
        INSERT INTO academic_sessions (
            tenant_id, name, start_date, end_date, status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session.tenant_id,
            session.name,
            session.start_date,
            session.end_date,
            session.status,
        ),
    )

    connection.commit()

    class_id = connection.execute(
        "SELECT id FROM academic_classes WHERE tenant_id = ? AND name = ?",
        (tenant_id, class_name),
    ).fetchone()["id"]
    subject_id = connection.execute(
        "SELECT id FROM academic_subjects WHERE tenant_id = ? AND name = ?",
        (tenant_id, f"Mathematics {class_name}"),
    ).fetchone()["id"]
    session_id = connection.execute(
        "SELECT id FROM academic_sessions WHERE tenant_id = ? AND name = ?",
        (tenant_id, f"2026/2027 {class_name}"),
    ).fetchone()["id"]

    term = AcademicTerm(
        id=None,
        tenant_id=tenant_id,
        academic_session_id=session_id,
        name=f"Term 1 {class_name}",
        start_date="2026-09-01",
        end_date="2026-12-18",
    )
    connection.execute(
        """
        INSERT INTO academic_terms (
            tenant_id, academic_session_id, name,
            start_date, end_date, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            term.tenant_id,
            term.academic_session_id,
            term.name,
            term.start_date,
            term.end_date,
            term.status,
        ),
    )
    connection.commit()

    term_id = connection.execute(
        """
        SELECT id FROM academic_terms
        WHERE tenant_id = ? AND name = ?
        """,
        (tenant_id, f"Term 1 {class_name}"),
    ).fetchone()["id"]

    offering = CourseOffering(
        id=None,
        tenant_id=tenant_id,
        academic_class_id=class_id,
        academic_subject_id=subject_id,
        academic_session_id=session_id,
        academic_term_id=term_id,
    )
    connection.execute(
        """
        INSERT INTO course_offerings (
            tenant_id, academic_class_id, academic_subject_id,
            academic_session_id, academic_term_id, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            offering.tenant_id,
            offering.academic_class_id,
            offering.academic_subject_id,
            offering.academic_session_id,
            offering.academic_term_id,
            offering.status,
        ),
    )
    connection.commit()

    offering_id = connection.execute(
        """
        SELECT id FROM course_offerings
        WHERE tenant_id = ?
          AND academic_class_id = ?
          AND academic_subject_id = ?
          AND academic_session_id = ?
          AND academic_term_id = ?
        """,
        (
            tenant_id,
            class_id,
            subject_id,
            session_id,
            term_id,
        ),
    ).fetchone()["id"]

    section = CourseSection(
        id=None,
        tenant_id=tenant_id,
        course_offering_id=offering_id,
        name=f"Section {class_name}",
    )
    connection.execute(
        """
        INSERT INTO course_sections (
            tenant_id, course_offering_id, name, status
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            section.tenant_id,
            section.course_offering_id,
            section.name,
            section.status,
        ),
    )
    connection.commit()

    return connection.execute(
        """
        SELECT id FROM course_sections
        WHERE tenant_id = ?
          AND course_offering_id = ?
          AND name = ?
        """,
        (
            tenant_id,
            offering_id,
            f"Section {class_name}",
        ),
    ).fetchone()["id"]


def test_create_and_get(connection):
    tenant_id = str(uuid.uuid4())
    _school(connection, tenant_id)
    student = _student(connection, tenant_id)
    section_id = _section(connection, tenant_id)

    repository = SectionStudentEnrollmentRepository(connection)

    enrollment = repository.create(
        SectionStudentEnrollment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section_id,
            student_id=student.id,
        )
    )

    loaded = repository.get(tenant_id, enrollment.id)

    assert loaded == enrollment


def test_get_is_tenant_scoped(connection):
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    _school(connection, tenant_a)
    _school(connection, tenant_b)

    student = _student(connection, tenant_a)
    section_id = _section(connection, tenant_a)

    repository = SectionStudentEnrollmentRepository(connection)

    enrollment = repository.create(
        SectionStudentEnrollment(
            id=None,
            tenant_id=tenant_a,
            course_section_id=section_id,
            student_id=student.id,
        )
    )

    assert repository.get(tenant_b, enrollment.id) is None


def test_list_is_section_scoped(connection):
    tenant_id = str(uuid.uuid4())
    _school(connection, tenant_id)

    student_one = _student(connection, tenant_id)
    student_two = _student(connection, tenant_id)

    section_one = _section(connection, tenant_id, "Class A")
    section_two = _section(connection, tenant_id, "Class B")

    repository = SectionStudentEnrollmentRepository(connection)

    repository.create(
        SectionStudentEnrollment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section_one,
            student_id=student_one.id,
        )
    )
    repository.create(
        SectionStudentEnrollment(
            id=None,
            tenant_id=tenant_id,
            course_section_id=section_two,
            student_id=student_two.id,
        )
    )

    rows = repository.list(tenant_id, section_one)

    assert len(rows) == 1
    assert rows[0].course_section_id == section_one
    assert rows[0].student_id == student_one.id


def test_cross_tenant_section_enrollment_rejected(connection):
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    _school(connection, tenant_a)
    _school(connection, tenant_b)

    student_a = _student(connection, tenant_a)
    section_a = _section(connection, tenant_a)

    repository = SectionStudentEnrollmentRepository(connection)

    with pytest.raises(Exception):
        repository.create(
            SectionStudentEnrollment(
                id=None,
                tenant_id=tenant_b,
                course_section_id=section_a,
                student_id=student_a.id,
            )
        )


def test_duplicate_student_assignment_rejected(connection):
    tenant_id = str(uuid.uuid4())
    _school(connection, tenant_id)

    student = _student(connection, tenant_id)
    section_id = _section(connection, tenant_id)

    repository = SectionStudentEnrollmentRepository(connection)

    enrollment = SectionStudentEnrollment(
        id=None,
        tenant_id=tenant_id,
        course_section_id=section_id,
        student_id=student.id,
    )

    repository.create(enrollment)

    with pytest.raises(Exception):
        repository.create(
            SectionStudentEnrollment(
                id=None,
                tenant_id=tenant_id,
                course_section_id=section_id,
                student_id=student.id,
            )
        )
