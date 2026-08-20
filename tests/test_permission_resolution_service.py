import sqlite3

from services.permission_resolution_service import (
    PermissionResolutionService,
)


def create_tables(connection):
    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
        """
    )

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


def seed(connection):
    connection.execute(
        """
        INSERT INTO users (tenant_id, name, email, role, status)
        VALUES ('tenant-a', 'Alice', 'alice@example.test', 'member', 'active')
        """
    )

    user_id = connection.execute(
        "SELECT id FROM users WHERE email = 'alice@example.test'"
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES ('tenant-a', 'teacher', 'active')
        """
    )

    role_id = connection.execute(
        "SELECT id FROM roles WHERE name = 'teacher'"
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES ('tenant-a', 'student.read', 'active')
        """
    )

    permission_id = connection.execute(
        "SELECT id FROM permissions WHERE name = 'student.read'"
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES ('tenant-a', ?, ?)
        """,
        (user_id, role_id),
    )

    connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES ('tenant-a', ?, ?)
        """,
        (role_id, permission_id),
    )

    connection.commit()

    return user_id, role_id, permission_id


def test_user_permission_is_resolved():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-a",
        permission_name="student.read",
    ) is True

    connection.close()


def test_unassigned_permission_is_denied():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-a",
        permission_name="student.write",
    ) is False

    connection.close()


def test_cross_tenant_permission_is_denied():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-b",
        permission_name="student.read",
    ) is False

    connection.close()


def test_authenticated_tenant_is_authoritative():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        permission_name="student.read",
    ) is True

    connection.close()


def test_get_permissions_returns_effective_permissions():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    service = PermissionResolutionService(connection)

    assert service.get_permissions(
        user_id=user_id,
        tenant_id="tenant-a",
    ) == {"student.read"}

    connection.close()


def test_inactive_user_has_no_permissions():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, _ = seed(connection)

    connection.execute(
        "UPDATE users SET status = 'inactive' WHERE id = ?",
        (user_id,),
    )
    connection.commit()

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-a",
        permission_name="student.read",
    ) is False

    assert service.get_permissions(
        user_id=user_id,
        tenant_id="tenant-a",
    ) == set()

    connection.close()


def test_inactive_role_has_no_permissions():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, role_id, _ = seed(connection)

    connection.execute(
        "UPDATE roles SET status = 'inactive' WHERE id = ?",
        (role_id,),
    )
    connection.commit()

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-a",
        permission_name="student.read",
    ) is False

    connection.close()


def test_inactive_permission_has_no_effective_access():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    user_id, _, permission_id = seed(connection)

    connection.execute(
        "UPDATE permissions SET status = 'inactive' WHERE id = ?",
        (permission_id,),
    )
    connection.commit()

    service = PermissionResolutionService(connection)

    assert service.has_permission(
        user_id=user_id,
        tenant_id="tenant-a",
        permission_name="student.read",
    ) is False

    connection.close()

def test_cross_tenant_user_role_link_is_rejected_by_schema():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            UNIQUE(id, tenant_id)
        );

        CREATE TABLE roles (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            UNIQUE(id, tenant_id)
        );

        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id),
            FOREIGN KEY (user_id, tenant_id)
                REFERENCES users(id, tenant_id),
            FOREIGN KEY (role_id, tenant_id)
                REFERENCES roles(id, tenant_id)
        );
    """)

    connection.execute("""
        INSERT INTO users
            (id, tenant_id, name, email, role, status)
        VALUES
            (1, 'tenant-a', 'Alice', 'alice@example.test', 'member', 'active')
    """)

    connection.execute("""
        INSERT INTO roles
            (id, tenant_id, name, status)
        VALUES
            (10, 'tenant-a', 'teacher', 'active')
    """)

    connection.commit()

    try:
        connection.execute("""
            INSERT INTO user_roles
                (tenant_id, user_id, role_id)
            VALUES
                ('tenant-b', 1, 10)
        """)
        connection.commit()
        assert False, "cross-tenant user-role link was incorrectly accepted"
    except sqlite3.IntegrityError:
        pass

    connection.close()


def test_cross_tenant_role_permission_link_is_rejected_by_schema():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            UNIQUE(id, tenant_id)
        );

        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            UNIQUE(id, tenant_id)
        );

        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id),
            FOREIGN KEY (role_id, tenant_id)
                REFERENCES roles(id, tenant_id),
            FOREIGN KEY (permission_id, tenant_id)
                REFERENCES permissions(id, tenant_id)
        );
    """)

    connection.execute("""
        INSERT INTO roles
            (id, tenant_id, name, status)
        VALUES
            (10, 'tenant-a', 'teacher', 'active')
    """)

    connection.execute("""
        INSERT INTO permissions
            (id, tenant_id, name, status)
        VALUES
            (20, 'tenant-a', 'student.read', 'active')
    """)

    connection.commit()

    try:
        connection.execute("""
            INSERT INTO role_permissions
                (tenant_id, role_id, permission_id)
            VALUES
                ('tenant-b', 10, 20)
        """)
        connection.commit()
        assert False, "cross-tenant role-permission link was incorrectly accepted"
    except sqlite3.IntegrityError:
        pass

    connection.close()
