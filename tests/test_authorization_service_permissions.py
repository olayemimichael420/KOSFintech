import sqlite3

from services.authorization_service import AuthorizationService


def create_tables(connection):
    connection.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        );

        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        );

        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        );
    """)


def seed(connection):
    connection.execute("""
        INSERT INTO users (tenant_id, name, email, role)
        VALUES ('tenant-a', 'Alice', 'alice@test.local', 'member')
    """)

    user_id = connection.execute(
        "SELECT id FROM users WHERE email = 'alice@test.local'"
    ).fetchone()[0]

    connection.execute("""
        INSERT INTO roles (tenant_id, name)
        VALUES ('tenant-a', 'teacher')
    """)
    role_id = connection.execute(
        "SELECT id FROM roles WHERE name = 'teacher'"
    ).fetchone()[0]

    connection.execute("""
        INSERT INTO permissions (tenant_id, name)
        VALUES ('tenant-a', 'student.read')
    """)
    permission_id = connection.execute(
        "SELECT id FROM permissions WHERE name = 'student.read'"
    ).fetchone()[0]

    connection.execute(
        "INSERT INTO user_roles VALUES (?, ?, ?)",
        ("tenant-a", user_id, role_id),
    )
    connection.execute(
        "INSERT INTO role_permissions VALUES (?, ?, ?)",
        ("tenant-a", role_id, permission_id),
    )
    connection.commit()

    return user_id


def test_authorization_service_resolves_permission():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id = seed(connection)
    service = AuthorizationService(connection)

    assert service.has_permission(
        user_id=user_id,
        permission_name="student.read",
        tenant_id="tenant-a",
    ) is True

    connection.close()


def test_authorization_service_rejects_cross_tenant_permission():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id = seed(connection)
    service = AuthorizationService(connection)

    assert service.has_permission(
        user_id=user_id,
        permission_name="student.read",
        tenant_id="tenant-b",
    ) is False

    connection.close()
