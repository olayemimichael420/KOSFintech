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

def test_owner_cannot_authorize_resource_in_another_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES ('tenant-002', 'Second School', 'school')
        """
    )
    connection.commit()

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
        action=Action.MANAGE_USERS,
        resource_id="2",
    )

    assert decision.allowed is False
    assert decision.reason == "resource administration mismatch"

    connection.close()

def test_owner_can_authorize_matching_administration_resource():
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
        action=Action.MANAGE_USERS,
        resource_id="1",
    )

    assert decision.allowed is True
    assert decision.reason == "owner authorized within administration"

    connection.close()


def test_admin1_cannot_authorize_resource_in_another_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES ('tenant-002', 'Second School', 'school')
        """
    )
    connection.commit()

    repository = AdministrationAuthorityRepository(connection)
    repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.ADMIN_1,
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
        action=Action.MANAGE_USERS,
        resource_id="2",
    )

    assert decision.allowed is False
    assert decision.reason == "resource administration mismatch"

    connection.close()

def test_super_admin_context_cannot_use_administration_action():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO platform_authorities (user_id, role, status)
        VALUES (1, 'super_admin', 'active')
        """
    )
    connection.commit()

    context_service = AuthorizationContextService(connection)
    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.is_super_admin is True

    authorization_service = AuthorizationService(connection)
    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.MANAGE_USERS,
    )

    assert decision.allowed is False
    assert decision.reason == "action is not permitted for super_admin"

    connection.close()


def test_super_admin_context_can_transfer_super_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO platform_authorities (user_id, role, status)
        VALUES (1, 'super_admin', 'active')
        """
    )
    connection.commit()

    context_service = AuthorizationContextService(connection)
    context = context_service.resolve(user_id=1)

    assert context.is_super_admin is True

    authorization_service = AuthorizationService(connection)
    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="2",
    )

    assert decision.allowed is True
    assert decision.reason == "super_admin authorized at platform level"

    connection.close()

def test_stale_super_admin_context_cannot_authorize_after_transfer():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO platform_authorities (user_id, role, status)
        VALUES (1, 'super_admin', 'active')
        """
    )
    connection.commit()

    context_service = AuthorizationContextService(connection)
    authorization_service = AuthorizationService(connection)

    # Resolve while user 1 is legitimately the active Super Admin.
    context = context_service.resolve(user_id=1)
    assert context.is_super_admin is True

    # Authority is subsequently transferred away from user 1.
    connection.execute(
        """
        UPDATE platform_authorities
        SET status = 'inactive',
            transferred_at = '2026-08-20T00:00:00+00:00'
        WHERE user_id = 1
          AND role = 'super_admin'
          AND status = 'active'
        """
    )
    connection.execute(
        """
        INSERT INTO platform_authorities (user_id, role, status)
        VALUES (2, 'super_admin', 'active')
        """
    )
    connection.commit()

    # The previously resolved context is now stale and must not
    # retain platform governance authority.
    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="3",
    )

    assert decision.allowed is False

    connection.close()


def test_stale_administration_context_cannot_authorize_after_deactivation():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute("""
        INSERT INTO administration_authorities (
            tenant_id, administration_id, user_id, role, status
        )
        VALUES ('tenant-001', 1, 1, 'owner', 'active')
    """)
    connection.commit()

    context_service = AuthorizationContextService(connection)
    authorization_service = AuthorizationService(connection)

    # User 1 legitimately has administration authority at resolution time.
    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role == "owner"
    assert context.has_administration_authority is True

    # Authority is subsequently revoked.
    connection.execute("""
        UPDATE administration_authorities
        SET status = 'inactive'
        WHERE tenant_id = 'tenant-001'
          AND administration_id = 1
          AND user_id = 1
          AND status = 'active'
    """)
    connection.commit()

    # The old context must no longer confer governance authority.
    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.MANAGE_USERS,
        resource_type="administration",
        resource_id="1",
    )

    assert decision.allowed is False

    connection.close()


def test_stale_super_admin_context_cannot_authorize_after_user_deactivation():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute("""
        INSERT INTO platform_authorities (user_id, role, status)
        VALUES (1, 'super_admin', 'active')
    """)
    connection.commit()

    context_service = AuthorizationContextService(connection)
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(user_id=1)

    assert context.is_super_admin is True

    connection.execute("""
        UPDATE users
        SET status = 'inactive'
        WHERE id = 1
    """)
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="2",
    )

    assert decision.allowed is False
    assert decision.reason == "authenticated user is inactive"

    connection.close()


def test_stale_administration_context_cannot_authorize_after_user_deactivation():
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
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role == "owner"
    assert context.has_administration_authority is True

    connection.execute("""
        UPDATE users
        SET status = 'inactive'
        WHERE id = 1
    """)
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.MANAGE_USERS,
        resource_type="administration",
        resource_id="1",
    )

    assert decision.allowed is False
    assert decision.reason == "authenticated user is inactive"

    connection.close()


def test_stale_owner_context_cannot_retain_owner_privileges_after_role_change():
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
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role == "owner"

    connection.execute(
        """
        UPDATE administration_authorities
        SET role = 'admin1'
        WHERE administration_id = 1
          AND user_id = 1
          AND status = 'active'
        """
    )
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is False


def test_stale_admin1_context_uses_current_role_after_promotion_to_owner():
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
            role=AdministrationAuthorityRole.ADMIN_1,
        )
    )

    context_service = AuthorizationContextService(connection)
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role == "admin1"

    connection.execute(
        """
        UPDATE administration_authorities
        SET role = 'owner'
        WHERE administration_id = 1
          AND user_id = 1
          AND status = 'active'
        """
    )
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.REMOVE_ADMIN,
    )

    assert decision.allowed is True
    assert decision.reason == "owner authorized within administration"


def test_stale_context_cannot_cross_tenant_after_user_tenant_change():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (
            'tenant-002',
            'Second School',
            'school'
        )
        """
    )

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
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(
        user_id=1,
        administration_id=1,
        tenant_id="tenant-001",
    )

    assert context.administration_role == "owner"

    connection.execute(
        """
        UPDATE users
        SET tenant_id = 'tenant-002'
        WHERE id = 1
        """
    )
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.MANAGE_USERS,
        resource_id="1",
    )

    assert decision.allowed is False


def test_stale_super_admin_context_cannot_survive_authority_deactivation():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute(
        """
        INSERT INTO platform_authorities (
            user_id,
            role,
            status
        )
        VALUES (1, 'super_admin', 'active')
        """
    )
    connection.commit()

    context_service = AuthorizationContextService(connection)
    authorization_service = AuthorizationService(connection)

    context = context_service.resolve(user_id=1)

    assert context.is_super_admin is True

    connection.execute(
        """
        UPDATE platform_authorities
        SET status = 'inactive'
        WHERE user_id = 1
          AND role = 'super_admin'
          AND status = 'active'
        """
    )
    connection.commit()

    decision = authorization_service.authorize_context(
        context=context,
        administration_id=1,
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="2",
    )

    assert decision.allowed is False
    assert decision.reason == "no active platform super admin authority"
