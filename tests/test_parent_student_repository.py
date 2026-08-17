import sqlite3

from models.parent_student import ParentStudentLink
from repositories.parent_student_repository import ParentStudentRepository


def test_create_and_get_parent_student_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE parent_students (
            parent_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (parent_id, student_id)
        )
        """
    )

    repository = ParentStudentRepository(connection)

    link = ParentStudentLink(
        parent_id=5001,
        student_id=1,
    )

    created = repository.create(link)

    assert created.parent_id == 5001
    assert created.student_id == 1

    result = repository.get(5001, 1)

    assert result is not None
    assert result.parent_id == 5001
    assert result.student_id == 1

    connection.close()
