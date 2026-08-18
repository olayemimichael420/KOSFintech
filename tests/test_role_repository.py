import sqlite3

from models.role import Role
from repositories.role_repository import RoleRepository


def test_create_and_get_role():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    repository = RoleRepository(connection)

    role = Role(
        id=None,
        tenant_id="school-001",
        name="teacher",
        description="Teaching staff",
    )

    created = repository.create(role)

    assert created.id is not None
    assert created.tenant_id == "school-001"
    assert created.name == "teacher"
    assert created.description == "Teaching staff"
    assert created.status == "active"

    result = repository.get(created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.name == "teacher"
    assert result.description == "Teaching staff"
    assert result.status == "active"

    connection.close()
