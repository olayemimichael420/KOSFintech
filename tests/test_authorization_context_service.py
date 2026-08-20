import sqlite3

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from models.platform_authority import (
    PlatformAuthority,
    PlatformAuthorityRole,
)
from services.authorization_context_service import (
    AuthorizationContextService,
)


def create_tables(connection):
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
        CREATE TABLE platform_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin')),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transferred_at TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE administration_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            administration_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'admin1', 'admin2')),
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(administration_id, role),
            UNIQUE(administration_id, user_id)
        )
    """)

    connection.execute("""
        INSERT INTO users (tenant_id, name, role)
        VALUES ('tenant-001', 'Test User', 'teacher')
    """)

    connection.commit()


def test_application_role_does_not_create_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    service = AuthorizationContextService(connection)

    context = service.resolve(user_id=1)

    assert context.user_id == 1
    assert context.platform_role is None
    assert context.administration_role is None

    connection.close()


def test_platform_super_admin_is_resolved():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.platform_authority_repository",
        fromlist=["PlatformAuthorityRepository"],
    ).PlatformAuthorityRepository(connection)

    repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    service = AuthorizationContextService(connection)

    context = service.resolve(user_id=1)

    assert context.is_super_admin is True
    assert context.platform_role == "super_admin"

    connection.close()


def test_administration_authority_is_resolved():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.administration_authority_repository",
        fromlist=["AdministrationAuthorityRepository"],
    ).AdministrationAuthorityRepository(connection)

    repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=10,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    service = AuthorizationContextService(connection)

    context = service.resolve(
        user_id=1,
        administration_id=10,
        tenant_id="tenant-001",
    )

    assert context.administration_id == 10
    assert context.administration_role == "owner"
    assert context.has_administration_authority is True

    connection.close()


def test_supplied_tenant_cannot_override_authenticated_users_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.administration_authority_repository",
        fromlist=["AdministrationAuthorityRepository"],
    ).AdministrationAuthorityRepository(connection)

    repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=10,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    service = AuthorizationContextService(connection)

    context = service.resolve(
        user_id=1,
        administration_id=10,
        tenant_id="tenant-002",
    )

    assert context.user_id == 1
    assert context.administration_id == 10
    assert context.administration_role is None
    assert context.has_administration_authority is False

    connection.close()


def test_authenticated_users_tenant_resolves_valid_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.administration_authority_repository",
        fromlist=["AdministrationAuthorityRepository"],
    ).AdministrationAuthorityRepository

    repository(connection).create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=10,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    service = AuthorizationContextService(connection)

    context = service.resolve(
        user_id=1,
        administration_id=10,
    )

    assert context.administration_role == "owner"
    assert context.has_administration_authority is True

    connection.close()

def test_supplied_tenant_cannot_select_cross_tenant_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.administration_authority_repository",
        fromlist=["AdministrationAuthorityRepository"],
    ).AdministrationAuthorityRepository(connection)

    # Authenticated user belongs to tenant-001.
    # Deliberately create an authority row claiming tenant-002.
    repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-002",
            administration_id=10,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    service = AuthorizationContextService(connection)

    context = service.resolve(
        user_id=1,
        administration_id=10,
        tenant_id="tenant-002",
    )

    assert context.user_id == 1
    assert context.administration_id == 10
    assert context.administration_role is None
    assert context.has_administration_authority is False

    connection.close()

def test_inactive_user_does_not_resolve_as_super_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = __import__(
        "repositories.platform_authority_repository",
        fromlist=["PlatformAuthorityRepository"],
    ).PlatformAuthorityRepository(connection)

    repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    connection.execute(
        """
        UPDATE users
        SET status = 'inactive'
        WHERE id = 1
        """
    )
    connection.commit()

    service = AuthorizationContextService(connection)
    context = service.resolve(user_id=1)

    assert context.is_super_admin is False
    assert context.platform_role is None

    connection.close()
