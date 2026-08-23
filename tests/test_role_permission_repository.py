import sqlite3

from models.role_permission import RolePermissionLink
from repositories.role_permission_repository import RolePermissionRepository


def test_create_and_get_role_permission_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        )
        """
    )

    repository = RolePermissionRepository(connection)

    link = RolePermissionLink(
        tenant_id="school-001",
        role_id=1,
        permission_id=1,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.role_id == 1
    assert created.permission_id == 1

    result = repository.get("school-001", 1, 1)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.role_id == 1
    assert result.permission_id == 1

    connection.close()


def test_get_role_permission_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        )
        """
    )

    repository = RolePermissionRepository(connection)

    repository.create(
        RolePermissionLink(
            tenant_id="school-A",
            role_id=1,
            permission_id=1,
        )
    )

    assert repository.get("school-A", 1, 1) is not None
    assert repository.get("school-B", 1, 1) is None

    connection.close()
