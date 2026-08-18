import sqlite3

from models.teacher_student import TeacherStudentLink
from repositories.teacher_student_repository import TeacherStudentRepository


def test_create_and_get_teacher_student_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE teacher_students (
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (teacher_id, student_id)
        )
        """
    )

    repository = TeacherStudentRepository(connection)

    link = TeacherStudentLink(
        teacher_id=2001,
        student_id=1,
    )

    created = repository.create(link)

    assert created.teacher_id == 2001
    assert created.student_id == 1

    result = repository.get(2001, 1)

    assert result is not None
    assert result.teacher_id == 2001
    assert result.student_id == 1

    connection.close()
