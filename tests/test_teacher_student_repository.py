import sqlite3

from models.teacher_student import TeacherStudentLink
from repositories.teacher_student_repository import TeacherStudentRepository


def test_create_and_get_teacher_student_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE teacher_students (
            tenant_id TEXT NOT NULL,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, teacher_id, student_id)
        )
        """
    )

    repository = TeacherStudentRepository(connection)

    link = TeacherStudentLink(
        tenant_id="school-001",
        teacher_id=2001,
        student_id=1,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.teacher_id == 2001
    assert created.student_id == 1

    result = repository.get("school-001", 2001, 1)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.teacher_id == 2001
    assert result.student_id == 1

    assert repository.get("school-002", 2001, 1) is None

    connection.close()
