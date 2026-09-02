import sqlite3

import pytest

from models.student import Student
from repositories.student_repository import StudentRepository
from services.student_service import StudentService


def create_schema(connection):
    connection.execute(
        """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            age INTEGER,
            guardian_id INTEGER,
            enrollment_date DATE,
            status TEXT DEFAULT 'active'
        )
        """
    )
    connection.commit()


def test_student_service_creates_student_for_bound_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        service = StudentService(
            StudentRepository(connection),
            tenant_id="school-001",
        )

        student = Student(
            id=None,
            tenant_id="school-001",
            user_id=None,
            name="Student A",
            class_name="JSS 1",
            age=12,
            guardian_id=None,
            enrollment_date="2026-08-29",
        )

        created = service.create(student)

        assert created.id is not None
        assert created.tenant_id == "school-001"

    finally:
        connection.close()


def test_student_service_rejects_cross_tenant_create():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        service = StudentService(
            StudentRepository(connection),
            tenant_id="school-001",
        )

        with pytest.raises(ValueError, match="student tenant mismatch"):
            service.create(
                Student(
                    id=None,
                    tenant_id="school-002",
                    user_id=None,
                    name="Student B",
                    class_name="JSS 1",
                    age=12,
                    guardian_id=None,
                    enrollment_date="2026-08-29",
                )
            )

    finally:
        connection.close()


def test_student_service_get_is_bound_to_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        repository = StudentRepository(connection)

        student = repository.create(
            Student(
                id=None,
                tenant_id="school-001",
                user_id=None,
                name="Student A",
                class_name="JSS 1",
                age=12,
                guardian_id=None,
                enrollment_date="2026-08-29",
            )
        )

        service = StudentService(
            repository,
            tenant_id="school-001",
        )

        assert service.get(student.id) is not None

        other_tenant_service = StudentService(
            repository,
            tenant_id="school-002",
        )

        assert other_tenant_service.get(student.id) is None

    finally:
        connection.close()
