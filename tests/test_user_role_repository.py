import sqlite3

from models.user_role import UserRoleLink
from repositories.user_role_repository import UserRoleRepository


def test_create_and_get_user_role_link():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        )
        """
    )

    repository = UserRoleRepository(connection)

    link = UserRoleLink(
        tenant_id="school-001",
        user_id=5001,
        role_id=1,
    )

    created = repository.create(link)

    assert created.tenant_id == "school-001"
    assert created.user_id == 5001
    assert created.role_id == 1

    result = repository.get("school-001", 5001, 1)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.user_id == 5001
    assert result.role_id == 1

    connection.close()


def test_get_user_role_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        )
        """
    )

    repository = UserRoleRepository(connection)

    repository.create(
        UserRoleLink(
            tenant_id="school-A",
            user_id=5001,
            role_id=1,
        )
    )

    assert repository.get("school-A", 5001, 1) is not None
    assert repository.get("school-B", 5001, 1) is None

    connection.close()
