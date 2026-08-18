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
            FOREIGN KEY (administration_id)
                REFERENCES administrations(id),
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    connection.execute("""
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
    """, (
        "tenant-001",
        "Example School",
        "school",
    ))

    connection.execute("""
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role
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
            tenant_id,
            name,
            email,
            role
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


def test_owner_decision_is_allowed():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)
    add_authority(connection, 1, 1, "owner")

    service = AuthorizationService(connection)

    decision = service.authorize_decision(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is True
    assert decision.reason == "owner authorized within administration"

    connection.close()


def test_admin_decision_is_allowed_for_user_management():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)
    add_authority(connection, 1, 2, "admin1")

    service = AuthorizationService(connection)

    decision = service.authorize_decision(
        user_id=2,
        administration_id=1,
        action=Action.MANAGE_USERS,
    )

    assert decision.allowed is True
    assert decision.reason == "administrator authorized within administration"

    connection.close()


def test_admin_decision_is_denied_for_remove_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)
    add_authority(connection, 1, 2, "admin1")

    service = AuthorizationService(connection)

    decision = service.authorize_decision(
        user_id=2,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is False
    assert decision.reason == "action is not permitted for administrator"

    connection.close()


def test_inactive_authority_has_explicit_reason():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)
    add_authority(
        connection,
        1,
        1,
        "owner",
        "inactive",
    )

    service = AuthorizationService(connection)

    decision = service.authorize_decision(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is False
    assert decision.reason == "no active authority assignment"

    connection.close()


def test_user_without_authority_has_explicit_reason():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    service = AuthorizationService(connection)

    decision = service.authorize_decision(
        user_id=1,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is False
    assert decision.reason == "no active authority assignment"

    connection.close()
