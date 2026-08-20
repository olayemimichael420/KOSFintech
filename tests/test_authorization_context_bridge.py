import sqlite3

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from models.authority import Action
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)
from services.authorization_context_service import (
    AuthorizationContextService,
)
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
        CREATE TABLE platform_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin')),
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transferred_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        CREATE UNIQUE INDEX ux_platform_authorities_active_role
        ON platform_authorities(role)
        WHERE status = 'active'
    """)

    connection.execute("""
        CREATE UNIQUE INDEX ux_platform_authorities_active_user
        ON platform_authorities(user_id)
        WHERE status = 'active'
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
        VALUES ('tenant-001', 'Example School', 'school')
    """)

    connection.execute("""
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role
        )
        VALUES (
            'tenant-001',
            'Owner User',
            'owner@example.com',
            'teacher'
        )
    """)

    connection.commit()


def test_context_bridge_allows_authorized_owner():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    context_service = AuthorizationContextService(connection)
    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    authorization_service = AuthorizationService(connection)

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is True
    assert decision.reason == "owner authorized within administration"

    connection.close()


def test_context_bridge_denies_user_without_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    context_service = AuthorizationContextService(connection)
    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    authorization_service = AuthorizationService(connection)

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is False
    assert decision.reason == "no active authority assignment"

    connection.close()


def test_application_role_is_not_used_as_governance_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    context_service = AuthorizationContextService(connection)
    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role is None

    authorization_service = AuthorizationService(connection)

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.MANAGE_USERS,
    )

    assert decision.allowed is False

    connection.close()
