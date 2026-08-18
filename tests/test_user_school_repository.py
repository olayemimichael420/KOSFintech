import sqlite3

from models.user_school import UserSchoolLink
from repositories.user_school_repository import UserSchoolRepository


def test_create_and_get_user_school_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE user_schools (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id)
        )
        """
    )

    repository = UserSchoolRepository(connection)

    link = UserSchoolLink(
        tenant_id="school-001",
        user_id=5001,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.user_id == 5001

    result = repository.get("school-001", 5001)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.user_id == 5001

    connection.close()
