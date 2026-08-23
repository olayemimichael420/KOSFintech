import sqlite3

from models.parent_student import ParentStudentLink
from repositories.parent_student_repository import ParentStudentRepository


def test_create_and_get_parent_student_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE parent_students (
            tenant_id TEXT NOT NULL,
            parent_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, parent_id, student_id)
        )
        """
    )

    repository = ParentStudentRepository(connection)

    link = ParentStudentLink(
        tenant_id="school-001",
        parent_id=5001,
        student_id=1,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.parent_id == 5001
    assert created.student_id == 1

    result = repository.get("school-001", 5001, 1)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.parent_id == 5001
    assert result.student_id == 1

    assert repository.get("school-002", 5001, 1) is None

    connection.close()
