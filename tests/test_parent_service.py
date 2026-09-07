import sqlite3

import pytest

from models.parent import Parent
from services.parent_service import ParentService


def test_parent_service_creates_parent_for_bound_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    service = ParentService(
        repository=__import__(
            "repositories.parent_repository",
            fromlist=["ParentRepository"],
        ).ParentRepository(connection),
        tenant_id="school-001",
    )

    parent = Parent(
        id=None,
        tenant_id="school-001",
        user_id=None,
        name="Jane Parent",
        phone="08000000000",
        email="jane@example.com",
    )

    created = service.create(parent)

    assert created.id is not None
    assert created.tenant_id == "school-001"


def test_parent_service_rejects_cross_tenant_create():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    class StubRepository:
        def create(self, parent):
            return parent

    service = ParentService(
        repository=StubRepository(),
        tenant_id="school-001",
    )

    parent = Parent(
        id=None,
        tenant_id="school-002",
        user_id=None,
        name="Other Parent",
        phone=None,
        email=None,
    )

    with pytest.raises(ValueError, match="parent tenant mismatch"):
        service.create(parent)


def test_parent_service_get_is_bound_to_tenant():
    class StubRepository:
        def get(self, tenant_id, parent_id):
            return tenant_id, parent_id

    service = ParentService(
        repository=StubRepository(),
        tenant_id="school-001",
    )

    result = service.get(42)

    assert result == ("school-001", 42)


def test_parent_service_allows_authorized_write():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
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
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        )
    """)

    connection.execute("""
        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        )
    """)

    user_id = connection.execute("""
        INSERT INTO users (tenant_id, name, role)
        VALUES ('school-001', 'Admin', 'admin')
    """).lastrowid

    role_id = connection.execute("""
        INSERT INTO roles (tenant_id, name)
        VALUES ('school-001', 'admin')
    """).lastrowid

    permission_id = connection.execute("""
        INSERT INTO permissions (tenant_id, name)
        VALUES ('school-001', 'parent.write')
    """).lastrowid

    connection.execute("""
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES ('school-001', ?, ?)
    """, (user_id, role_id))

    connection.execute("""
        INSERT INTO role_permissions (tenant_id, role_id, permission_id)
        VALUES ('school-001', ?, ?)
    """, (role_id, permission_id))

    connection.commit()

    from repositories.parent_repository import ParentRepository

    service = ParentService(
        repository=ParentRepository(connection),
        tenant_id="school-001",
        connection=connection,
        user_id=user_id,
    )

    created = service.create(
        Parent(
            id=None,
            tenant_id="school-001",
            user_id=None,
            name="Authorized Parent",
            phone=None,
            email=None,
        )
    )

    assert created.id is not None


def test_parent_service_denies_missing_write_permission():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
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
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    connection.execute("""
        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        )
    """)

    connection.execute("""
        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        )
    """)

    user_id = connection.execute("""
        INSERT INTO users (tenant_id, name, role)
        VALUES ('school-001', 'No Permission', 'user')
    """).lastrowid

    connection.commit()

    from repositories.parent_repository import ParentRepository

    service = ParentService(
        repository=ParentRepository(connection),
        tenant_id="school-001",
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(PermissionError, match="parent.write"):
        service.create(
            Parent(
                id=None,
                tenant_id="school-001",
                user_id=None,
                name="Denied Parent",
                phone=None,
                email=None,
            )
        )



def test_parent_service_list_is_bound_to_tenant():
    class Repository:
        def list(self, tenant_id):
            return [tenant_id]

    service = ParentService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    assert service.list() == ["school-001"]



def test_parent_service_list_is_bound_to_tenant():
    class Repository:
        def list(self, tenant_id):
            return [tenant_id]

    service = ParentService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    assert service.list() == ["school-001"]



def test_parent_service_list_denies_missing_read_permission():
    class Repository:
        def list(self, tenant_id):
            return []

    service = ParentService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    service.permission_service = type(
        "PermissionService",
        (),
        {"has_permission": lambda *args, **kwargs: False},
    )()
    service.user_id = 1

    with pytest.raises(PermissionError, match="missing permission: parent.read"):
        service.list()
