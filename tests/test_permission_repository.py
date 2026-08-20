import sqlite3

from models.permission import Permission
from repositories.permission_repository import PermissionRepository


def test_create_and_get_permission():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    repository = PermissionRepository(connection)

    permission = Permission(
        id=None,
        tenant_id="school-001",
        name="student.read",
        description="View student records",
    )

    created = repository.create(permission)

    assert created.id is not None
    assert created.tenant_id == "school-001"
    assert created.name == "student.read"
    assert created.description == "View student records"
    assert created.status == "active"

    result = repository.get("school-001", created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.name == "student.read"
    assert result.description == "View student records"
    assert result.status == "active"

    connection.close()
