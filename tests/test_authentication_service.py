import sqlite3

from services.authentication_service import (
    AuthenticationService,
    AuthenticatedIdentity,
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
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-001",
            "Test User",
            "test@example.com",
            "teacher",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-002",
            "Inactive User",
            "inactive@example.com",
            "member",
            "inactive",
        ),
    )

    connection.commit()


def test_active_user_authenticates():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    service = AuthenticationService(connection)

    identity = service.authenticate(user_id=1)

    assert identity is not None
    assert isinstance(identity, AuthenticatedIdentity)
    assert identity.user_id == 1
    assert identity.tenant_id == "tenant-001"
    assert identity.is_authenticated is True

    connection.close()


def test_unknown_user_does_not_authenticate():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    service = AuthenticationService(connection)

    identity = service.authenticate(user_id=999)

    assert identity is None

    connection.close()


def test_inactive_user_does_not_authenticate():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    service = AuthenticationService(connection)

    identity = service.authenticate(user_id=2)

    assert identity is None

    connection.close()


def test_authentication_does_not_use_application_role_as_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        UPDATE users
        SET role = 'owner'
        WHERE id = 1
        """
    )
    connection.commit()

    service = AuthenticationService(connection)

    identity = service.authenticate(user_id=1)

    assert identity is not None
    assert identity.user_id == 1
    assert identity.tenant_id == "tenant-001"

    assert not hasattr(identity, "role")
    assert not hasattr(identity, "authority")

    connection.close()


def test_authenticated_identity_is_immutable():
    identity = AuthenticatedIdentity(
        user_id=1,
        tenant_id="tenant-001",
    )

    try:
        identity.user_id = 99
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "AuthenticatedIdentity must be immutable"
        )
