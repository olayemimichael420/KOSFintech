import sqlite3

import pytest

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)


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
            name TEXT NOT NULL
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
            UNIQUE(administration_id, user_id),
            FOREIGN KEY (administration_id)
                REFERENCES administrations(id),
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    connection.execute("""
        INSERT INTO administrations (
            tenant_id, name, administration_type
        )
        VALUES ('tenant-001', 'Tenant One', 'school')
    """)

    connection.execute("""
        INSERT INTO users (
            tenant_id, name
        )
        VALUES ('tenant-001', 'Tenant One User')
    """)

    connection.commit()


def make_authority(connection):
    repository = AdministrationAuthorityRepository(connection)

    return repository.create(
        AdministrationAuthority(
            id=None,
            tenant_id="tenant-001",
            administration_id=1,
            user_id=1,
            role=AdministrationAuthorityRole.OWNER,
        )
    )


def test_get_requires_matching_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    authority = make_authority(connection)
    repository = AdministrationAuthorityRepository(connection)

    result = repository.get(
        tenant_id="tenant-002",
        authority_id=authority.id,
    )

    assert result is None

    connection.close()


def test_get_returns_authority_for_matching_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    authority = make_authority(connection)
    repository = AdministrationAuthorityRepository(connection)

    result = repository.get(
        tenant_id="tenant-001",
        authority_id=authority.id,
    )

    assert result == authority

    connection.close()


def test_deactivate_requires_matching_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    authority = make_authority(connection)
    repository = AdministrationAuthorityRepository(connection)

    result = repository.deactivate(
        tenant_id="tenant-002",
        authority_id=authority.id,
    )

    assert result is None

    still_active = repository.get(
        tenant_id="tenant-001",
        authority_id=authority.id,
    )

    assert still_active is not None
    assert still_active.status == "active"

    connection.close()


def test_deactivate_works_for_matching_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    authority = make_authority(connection)
    repository = AdministrationAuthorityRepository(connection)

    result = repository.deactivate(
        tenant_id="tenant-001",
        authority_id=authority.id,
    )

    assert result is not None
    assert result.status == "inactive"

    connection.close()
