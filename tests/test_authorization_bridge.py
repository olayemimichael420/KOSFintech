import sqlite3

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from models.authority import (
    Action,
    ActorType,
    AuthorizationRequest,
    AuthorityRole,
    JurisdictionType,
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
        """
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role
        )
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-001", "Owner User", "owner@example.com", "member"),
    )

    connection.commit()


def test_active_owner_maps_to_owner_authority():
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

    assignment = repository.get_active_by_user_and_administration(
        tenant_id="tenant-001",
        user_id=1,
        administration_id=1,
    )

    assert assignment is not None
    assert assignment.user_id == 1
    assert assignment.administration_id == 1
    assert assignment.role == AdministrationAuthorityRole.OWNER
    assert assignment.status == "active"

    authority_role = AuthorityRole(assignment.role.value)

    assert authority_role == AuthorityRole.OWNER

    connection.close()


def test_inactive_authority_does_not_produce_active_assignment():
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

    repository.deactivate(authority.id)

    assignment = repository.get_active_by_user_and_administration(
        tenant_id="tenant-001",
        user_id=1,
        administration_id=1,
    )

    assert assignment is None

    connection.close()


def test_authorization_request_uses_administration_jurisdiction():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    repository = AdministrationAuthorityRepository(connection)

    assignment = repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )

    authority = assignment

    request = AuthorizationRequest(
        authority=__import__(
            "models.authority",
            fromlist=["Authority"],
        ).Authority(
            actor_id=authority.user_id,
            actor_type=ActorType.HUMAN,
            role=AuthorityRole(authority.role.value),
            jurisdiction_type=JurisdictionType.ADMINISTRATION,
            jurisdiction_id=str(authority.administration_id),
            administration_id=str(authority.administration_id),
        ),
        action=Action.REMOVE_ADMIN,
        resource_type="administration",
        resource_id=str(authority.administration_id),
    )

    assert request.authority.actor_id == 1
    assert request.authority.role == AuthorityRole.OWNER
    assert request.authority.jurisdiction_type == JurisdictionType.ADMINISTRATION

    connection.close()
