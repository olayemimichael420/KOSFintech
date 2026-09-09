import sqlite3

import pytest

from models.permission import Permission
from models.role import Role
from services.rbac_provisioning_service import RBACProvisioningService

from tests.test_authorization_service import create_tables, add_authority


def setup_connection():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    connection.execute("""
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_id INTEGER,
            tenant_id TEXT,
            action TEXT,
            metadata TEXT NOT NULL DEFAULT '{}'
        )
    """)

    connection.execute("""
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            UNIQUE(id, tenant_id)
        )
    """)

    connection.execute("""
        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id),
            FOREIGN KEY (user_id, tenant_id)
                REFERENCES users(id, tenant_id),
            FOREIGN KEY (role_id, tenant_id)
                REFERENCES roles(id, tenant_id)
        )
    """)

    connection.execute("""
        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            UNIQUE(id, tenant_id)
        )
    """)

    connection.execute("""
        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id),
            FOREIGN KEY (role_id, tenant_id)
                REFERENCES roles(id, tenant_id),
            FOREIGN KEY (permission_id, tenant_id)
                REFERENCES permissions(id, tenant_id)
        )
    """)

    connection.commit()

    add_authority(connection, 1, 1, "owner")
    return connection


def test_owner_can_create_role():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    role = Role(
        id=None,
        tenant_id="tenant-001",
        name="Teacher",
        description="Teacher application role",
    )

    created = service.create_role(
        user_id=1,
        administration_id=1,
        role=role,
    )

    assert created.id is not None
    assert created.tenant_id == "tenant-001"
    assert created.name == "Teacher"

    row = connection.execute(
        """
        SELECT event_type, actor_id, tenant_id
        FROM audit_events
        WHERE event_type = 'rbac_role_created'
        """
    ).fetchone()

    assert row is not None
    assert row["actor_id"] == 1
    assert row["tenant_id"] == "tenant-001"

    connection.close()


def test_owner_can_create_permission():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    permission = Permission(
        id=None,
        tenant_id="tenant-001",
        name="student.read",
        description="Read students",
    )

    created = service.create_permission(
        user_id=1,
        administration_id=1,
        permission=permission,
    )

    assert created.id is not None
    assert created.name == "student.read"

    row = connection.execute(
        """
        SELECT event_type, actor_id, tenant_id
        FROM audit_events
        WHERE event_type = 'rbac_permission_created'
        """
    ).fetchone()

    assert row is not None
    assert row["actor_id"] == 1
    assert row["tenant_id"] == "tenant-001"

    connection.close()


def test_owner_can_assign_role_to_same_tenant_user():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    role = service.create_role(
        user_id=1,
        administration_id=1,
        role=Role(
            id=None,
            tenant_id="tenant-001",
            name="Teacher",
        ),
    )

    link = service.assign_role_to_user(
        user_id=1,
        administration_id=1,
        target_user_id=2,
        role_id=role.id,
    )

    assert link.tenant_id == "tenant-001"
    assert link.user_id == 2
    assert link.role_id == role.id

    row = connection.execute(
        """
        SELECT event_type, actor_id, tenant_id
        FROM audit_events
        WHERE event_type = 'rbac_role_assigned'
        """
    ).fetchone()

    assert row is not None
    assert row["actor_id"] == 1
    assert row["tenant_id"] == "tenant-001"

    connection.close()


def test_owner_can_grant_permission_to_role():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    role = service.create_role(
        user_id=1,
        administration_id=1,
        role=Role(
            id=None,
            tenant_id="tenant-001",
            name="Teacher",
        ),
    )

    permission = service.create_permission(
        user_id=1,
        administration_id=1,
        permission=Permission(
            id=None,
            tenant_id="tenant-001",
            name="student.read",
        ),
    )

    link = service.grant_permission_to_role(
        user_id=1,
        administration_id=1,
        role_id=role.id,
        permission_id=permission.id,
    )

    assert link.tenant_id == "tenant-001"
    assert link.role_id == role.id
    assert link.permission_id == permission.id

    row = connection.execute(
        """
        SELECT event_type, actor_id, tenant_id
        FROM audit_events
        WHERE event_type = 'rbac_permission_granted'
        """
    ).fetchone()

    assert row is not None
    assert row["actor_id"] == 1
    assert row["tenant_id"] == "tenant-001"

    connection.close()


def test_non_authorized_user_cannot_create_role():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    with pytest.raises(PermissionError):
        service.create_role(
            user_id=2,
            administration_id=1,
            role=Role(
                id=None,
                tenant_id="tenant-001",
                name="Teacher",
            ),
        )

    count = connection.execute(
        "SELECT COUNT(*) FROM roles"
    ).fetchone()[0]

    assert count == 0
    connection.close()


def test_role_tenant_mismatch_is_rejected_without_mutation():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    with pytest.raises(ValueError, match="role tenant mismatch"):
        service.create_role(
            user_id=1,
            administration_id=1,
            role=Role(
                id=None,
                tenant_id="tenant-002",
                name="Teacher",
            ),
        )

    count = connection.execute(
        "SELECT COUNT(*) FROM roles"
    ).fetchone()[0]

    assert count == 0
    connection.close()


def test_permission_tenant_mismatch_is_rejected_without_mutation():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    with pytest.raises(ValueError, match="permission tenant mismatch"):
        service.create_permission(
            user_id=1,
            administration_id=1,
            permission=Permission(
                id=None,
                tenant_id="tenant-002",
                name="student.read",
            ),
        )

    count = connection.execute(
        "SELECT COUNT(*) FROM permissions"
    ).fetchone()[0]

    assert count == 0
    connection.close()


def test_cross_tenant_target_user_cannot_receive_role():
    connection = setup_connection()

    connection.execute("""
        INSERT INTO users (id, tenant_id, name, role, status)
        VALUES (3, 'tenant-002', 'Tenant Two User', 'member', 'active')
    """)

    connection.commit()

    service = RBACProvisioningService(connection)

    role = service.create_role(
        user_id=1,
        administration_id=1,
        role=Role(
            id=None,
            tenant_id="tenant-001",
            name="Teacher",
        ),
    )

    with pytest.raises(ValueError, match="target user not found"):
        service.assign_role_to_user(
            user_id=1,
            administration_id=1,
            target_user_id=3,
            role_id=role.id,
        )

    count = connection.execute(
        "SELECT COUNT(*) FROM user_roles"
    ).fetchone()[0]

    assert count == 0
    connection.close()


def test_missing_role_cannot_receive_permission():
    connection = setup_connection()
    service = RBACProvisioningService(connection)

    permission = service.create_permission(
        user_id=1,
        administration_id=1,
        permission=Permission(
            id=None,
            tenant_id="tenant-001",
            name="student.read",
        ),
    )

    with pytest.raises(ValueError, match="role not found"):
        service.grant_permission_to_role(
            user_id=1,
            administration_id=1,
            role_id=9999,
            permission_id=permission.id,
        )

    count = connection.execute(
        "SELECT COUNT(*) FROM role_permissions"
    ).fetchone()[0]

    assert count == 0
    connection.close()
