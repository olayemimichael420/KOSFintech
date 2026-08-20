import sqlite3

import pytest

import database


def _create_tenant_data(connection):
    users = {}

    for tenant_id, email in (
        ("tenant-a", "alice@tenant-a.test"),
        ("tenant-b", "bob@tenant-b.test"),
    ):
        connection.execute(
            """
            INSERT INTO users (
                tenant_id, name, email, role, status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                tenant_id.title(),
                email,
                "member",
                "active",
            ),
        )

        users[tenant_id] = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ? AND email = ?
            """,
            (tenant_id, email),
        ).fetchone()["id"]

    roles = {}

    for tenant_id in ("tenant-a", "tenant-b"):
        connection.execute(
            """
            INSERT INTO roles (
                tenant_id, name, description, status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                tenant_id,
                "teacher",
                f"Teacher role for {tenant_id}",
                "active",
            ),
        )

        roles[tenant_id] = connection.execute(
            """
            SELECT id
            FROM roles
            WHERE tenant_id = ? AND name = ?
            """,
            (tenant_id, "teacher"),
        ).fetchone()["id"]

    permissions = {}

    for tenant_id in ("tenant-a", "tenant-b"):
        connection.execute(
            """
            INSERT INTO permissions (
                tenant_id, name, description, status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                tenant_id,
                "student.read",
                f"Read students for {tenant_id}",
                "active",
            ),
        )

        permissions[tenant_id] = connection.execute(
            """
            SELECT id
            FROM permissions
            WHERE tenant_id = ? AND name = ?
            """,
            (tenant_id, "student.read"),
        ).fetchone()["id"]

    connection.commit()

    return users, roles, permissions


@pytest.fixture
def connection(tmp_path, monkeypatch):
    db_path = tmp_path / "rbac_tenant_isolation.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()

    connection = database.get_connection()

    try:
        yield connection
    finally:
        connection.close()


def test_user_role_rejects_cross_tenant_user(connection):
    users, roles, _ = _create_tenant_data(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO user_roles (
                tenant_id, user_id, role_id
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-a",
                users["tenant-b"],
                roles["tenant-a"],
            ),
        )


def test_user_role_rejects_cross_tenant_role(connection):
    users, roles, _ = _create_tenant_data(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO user_roles (
                tenant_id, user_id, role_id
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-a",
                users["tenant-a"],
                roles["tenant-b"],
            ),
        )


def test_role_permission_rejects_cross_tenant_role(connection):
    _, roles, permissions = _create_tenant_data(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id, role_id, permission_id
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-a",
                roles["tenant-b"],
                permissions["tenant-a"],
            ),
        )


def test_role_permission_rejects_cross_tenant_permission(connection):
    _, roles, permissions = _create_tenant_data(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id, role_id, permission_id
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-a",
                roles["tenant-a"],
                permissions["tenant-b"],
            ),
        )


def test_same_tenant_rbac_assignments_are_allowed(connection):
    users, roles, permissions = _create_tenant_data(connection)

    connection.execute(
        """
        INSERT INTO user_roles (
            tenant_id, user_id, role_id
        )
        VALUES (?, ?, ?)
        """,
        (
            "tenant-a",
            users["tenant-a"],
            roles["tenant-a"],
        ),
    )

    connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id, role_id, permission_id
        )
        VALUES (?, ?, ?)
        """,
        (
            "tenant-a",
            roles["tenant-a"],
            permissions["tenant-a"],
        ),
    )

    connection.commit()

    user_role = connection.execute(
        """
        SELECT *
        FROM user_roles
        WHERE tenant_id = ?
        """,
        ("tenant-a",),
    ).fetchone()

    role_permission = connection.execute(
        """
        SELECT *
        FROM role_permissions
        WHERE tenant_id = ?
        """,
        ("tenant-a",),
    ).fetchone()

    assert user_role is not None
    assert role_permission is not None
