import sqlite3

from models.platform_authority import (
    PlatformAuthority,
    PlatformAuthorityRole,
)
from repositories.platform_authority_repository import (
    PlatformAuthorityRepository,
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
            status TEXT DEFAULT 'active'
        )
        """
    )

    connection.execute(
        """
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
        """
    )

    connection.execute(
        """
        CREATE UNIQUE INDEX ux_platform_authorities_active_role
        ON platform_authorities(role)
        WHERE status = 'active'
        """
    )

    connection.execute(
        """
        CREATE UNIQUE INDEX ux_platform_authorities_active_user
        ON platform_authorities(user_id)
        WHERE status = 'active'
        """
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
        (
            "platform",
            "Platform Admin",
            "admin@example.com",
            "member",
        ),
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
        (
            "platform",
            "Second Admin",
            "admin2@example.com",
            "member",
        ),
    )

    connection.commit()


def test_create_and_get_platform_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = PlatformAuthorityRepository(connection)

    authority = PlatformAuthority(
        id=None,
        user_id=1,
        role=PlatformAuthorityRole.SUPER_ADMIN,
    )

    created = repository.create(authority)

    assert created.id is not None
    assert created.user_id == 1
    assert created.role == PlatformAuthorityRole.SUPER_ADMIN
    assert created.status == "active"

    fetched = repository.get(created.id)

    assert fetched == created

    connection.close()


def test_get_active_super_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = PlatformAuthorityRepository(connection)

    created = repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    active = repository.get_active_super_admin()

    assert active is not None
    assert active.id == created.id
    assert active.user_id == 1

    connection.close()


def test_get_active_by_user():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = PlatformAuthorityRepository(connection)

    repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    active = repository.get_active_by_user(1)

    assert active is not None
    assert active.user_id == 1
    assert active.role == PlatformAuthorityRole.SUPER_ADMIN

    connection.close()


def test_deactivate_platform_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = PlatformAuthorityRepository(connection)

    created = repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    repository.deactivate(
        created.id,
        transferred_at="2026-08-18T00:00:00+00:00",
    )

    inactive = repository.get(created.id)

    assert inactive is not None
    assert inactive.status == "inactive"
    assert inactive.transferred_at == "2026-08-18T00:00:00+00:00"

    assert repository.get_active_super_admin() is None

    connection.close()


def test_database_prevents_two_active_super_admins():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = PlatformAuthorityRepository(connection)

    repository.create(
        PlatformAuthority(
            id=None,
            user_id=1,
            role=PlatformAuthorityRole.SUPER_ADMIN,
        )
    )

    try:
        repository.create(
            PlatformAuthority(
                id=None,
                user_id=2,
                role=PlatformAuthorityRole.SUPER_ADMIN,
            )
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "Database allowed two active Super Admins"
        )

    connection.close()
