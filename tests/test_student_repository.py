import sqlite3

from models.student import Student
from repositories.student_repository import StudentRepository


def test_create_and_get_student():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

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

    repository = StudentRepository(connection)

    student = Student(
        id=None,
        tenant_id="school-001",
        user_id=1001,
        name="Test Student",
        class_name="JSS 1",
        age=12,
        guardian_id=5001,
        enrollment_date="2026-08-18",
    )

    created = repository.create(student)

    assert created.id is not None

    result = repository.get("school-001", created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.user_id == 1001
    assert result.name == "Test Student"
    assert result.class_name == "JSS 1"
    assert result.age == 12
    assert result.guardian_id == 5001
    assert result.enrollment_date == "2026-08-18"
    assert result.status == "active"

    connection.close()


def test_student_repository_cannot_read_student_from_another_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

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

    try:
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

        assert repository.get(
            "school-001",
            student.id,
        ) is not None

        assert repository.get(
            "school-002",
            student.id,
        ) is None

    finally:
        connection.close()
