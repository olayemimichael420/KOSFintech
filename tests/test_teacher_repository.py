import sqlite3

from models.teacher import Teacher
from repositories.teacher_repository import TeacherRepository


def test_create_and_get_teacher():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            qualification TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    repository = TeacherRepository(connection)

    teacher = Teacher(
        id=None,
        tenant_id="school-001",
        user_id=2001,
        name="Test Teacher",
        subject="Mathematics",
        qualification="B.Ed Mathematics",
    )

    created = repository.create(teacher)

    assert created.id is not None

    result = repository.get("school-001", created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.user_id == 2001
    assert result.name == "Test Teacher"
    assert result.subject == "Mathematics"
    assert result.qualification == "B.Ed Mathematics"
    assert result.status == "active"

    connection.close()
