import sqlite3

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)


def create_tables(connection):
    connection.execute(
        """
        CREATE TABLE administrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            administration_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
    )

    connection.execute(
        """
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
            FOREIGN KEY (administration_id) REFERENCES administrations(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "Example School", "school"),
    )

    connection.execute(
        "INSERT INTO users DEFAULT VALUES"
    )

    connection.execute(
        "INSERT INTO users DEFAULT VALUES"
    )

    connection.commit()


def test_create_and_get_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    authority = AdministrationAuthority(
        id=None,
        tenant_id="tenant-001",
        administration_id=1,
        user_id=1,
        role=AdministrationAuthorityRole.OWNER,
    )

    created = repository.create(authority)

    assert created.id is not None
    assert created.administration_id == 1
    assert created.user_id == 1
    assert created.role == AdministrationAuthorityRole.OWNER
    assert created.status == "active"

    fetched = repository.get(tenant_id="tenant-001", authority_id=created.id)

    assert fetched == created

    connection.close()


def test_get_active_authority_by_user_and_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    authority = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    result = repository.get_active_by_user_and_administration(
        tenant_id="tenant-001",
        user_id=1,
        administration_id=1,
    )

    assert result == authority

    connection.close()


def test_get_active_authority_by_role():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    authority = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    result = repository.get_active_by_administration_and_role(
        tenant_id="tenant-001",
        administration_id=1,
        role=AdministrationAuthorityRole.OWNER,
    )

    assert result == authority

    connection.close()


def test_list_authorities_by_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    owner = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    admin = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=2,
            role=AdministrationAuthorityRole.ADMIN_1,
        )
    )

    authorities = repository.list_by_administration("tenant-001", 1)

    assert len(authorities) == 2
    assert authorities[0] == owner
    assert authorities[1] == admin

    connection.close()


def test_deactivate_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    authority = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    deactivated = repository.deactivate(tenant_id="tenant-001", authority_id=authority.id)

    assert deactivated is not None
    assert deactivated.status == "inactive"

    active = repository.get_active_by_user_and_administration(
        tenant_id="tenant-001",
        user_id=1,
        administration_id=1,
    )

    assert active is None

    connection.close()
