import sqlite3

from models.authority import Action
from services.authorization_service import AuthorizationService


def create_tables(connection):
    connection.execute("""
        CREATE TABLE administrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            administration_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE administration_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            administration_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'admin1', 'admin2')),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(administration_id, role),
            UNIQUE(administration_id, user_id),
            FOREIGN KEY (administration_id) REFERENCES administrations(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        INSERT INTO administrations (
            tenant_id, name, administration_type
        )
        VALUES (?, ?, ?)
    """, ("tenant-001", "Example School", "school"))

    connection.execute("""
        INSERT INTO users (
            tenant_id, name, email, role
        )
        VALUES (?, ?, ?, ?)
    """, (
        "tenant-001",
        "Owner User",
        "owner@example.com",
        "member",
    ))

    connection.execute("""
        INSERT INTO users (
            tenant_id, name, email, role
        )
        VALUES (?, ?, ?, ?)
    """, (
        "tenant-001",
        "Admin User",
        "admin@example.com",
        "member",
    ))

    connection.commit()


def add_authority(
    connection,
    administration_id,
    user_id,
    role,
    status="active",
):
    connection.execute("""
        INSERT INTO administration_authorities (
            administration_id,
            user_id,
            role,
            status
        )
        VALUES (?, ?, ?, ?)
    """, (
        administration_id,
        user_id,
        role,
        status,
    ))
    connection.commit()


def test_active_owner_can_remove_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    add_authority(connection, 1, 1, "owner")

    service = AuthorizationService(connection)

    assert service.authorize(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    connection.close()


def test_active_admin_can_manage_users():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    add_authority(connection, 1, 2, "admin1")

    service = AuthorizationService(connection)

    assert service.authorize(
        user_id=2,
        administration_id=1,
        action=Action.MANAGE_USERS,
    )

    connection.close()


def test_inactive_authority_is_denied():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    add_authority(connection, 1, 1, "owner", "inactive")

    service = AuthorizationService(connection)

    assert not service.authorize(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    connection.close()


def test_user_without_authority_is_denied():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    service = AuthorizationService(connection)

    assert not service.authorize(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    connection.close()


def test_owner_cannot_suspend_platform():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    add_authority(connection, 1, 1, "owner")

    service = AuthorizationService(connection)

    assert not service.authorize(
        user_id=1,
        administration_id=1,
        action=Action.SUSPEND_ADMINISTRATION,
    )

    connection.close()


def test_admin_cannot_remove_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    add_authority(connection, 1, 2, "admin1")

    service = AuthorizationService(connection)

    assert not service.authorize(
        user_id=2,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    connection.close()
