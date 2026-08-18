import sqlite3

from models.school_teacher import SchoolTeacherLink
from repositories.school_teacher_repository import SchoolTeacherRepository


def test_create_and_get_school_teacher_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE school_teachers (
            tenant_id TEXT NOT NULL,
            teacher_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, teacher_id)
        )
        """
    )

    repository = SchoolTeacherRepository(connection)

    link = SchoolTeacherLink(
        tenant_id="school-001",
        teacher_id=2001,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.teacher_id == 2001

    result = repository.get("school-001", 2001)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.teacher_id == 2001

    connection.close()
