import sqlite3

from models.school_student import SchoolStudentLink
from repositories.school_student_repository import SchoolStudentRepository


def test_create_and_get_school_student_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE school_students (
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, student_id)
        )
        """
    )

    repository = SchoolStudentRepository(connection)

    link = SchoolStudentLink(
        tenant_id="school-001",
        student_id=3001,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.student_id == 3001

    result = repository.get("school-001", 3001)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.student_id == 3001

    connection.close()
