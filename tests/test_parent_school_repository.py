import sqlite3

from models.parent_school import ParentSchoolLink
from repositories.parent_school_repository import ParentSchoolRepository


def test_create_and_get_parent_school_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE parent_schools (
            tenant_id TEXT NOT NULL,
            parent_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, parent_id)
        )
        """
    )

    repository = ParentSchoolRepository(connection)

    link = ParentSchoolLink(
        tenant_id="school-001",
        parent_id=4001,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.parent_id == 4001

    result = repository.get("school-001", 4001)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.parent_id == 4001

    connection.close()
