import sqlite3

from models.administration import Administration
from repositories.administration_repository import AdministrationRepository
from services.administration_context_service import (
    AdministrationContextService,
)


def create_tables(connection):
    connection.execute("""
        CREATE TABLE administrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            administration_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        CREATE TABLE administration_authorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            administration_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    connection.commit()


def seed_user(
    connection,
    tenant_id="tenant-001",
    status="active",
):
    cursor = connection.execute(
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
            tenant_id,
            "Test User",
            "test@example.com",
            "teacher",
            status,
        ),
    )
    connection.commit()
    return cursor.lastrowid


def seed_administration(
    connection,
    tenant_id="tenant-001",
    status="active",
):
    repository = AdministrationRepository(connection)

    return repository.create(
        Administration(
            id=None,
            tenant_id=tenant_id,
            name="Test Administration",
            administration_type="school",
            status=status,
        )
    )


def test_administration_context_resolves_explicit_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)
        administration = seed_administration(connection)
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is not None
        assert context.user_id == user_id
        assert context.tenant_id == "tenant-001"
        assert context.administration_id == administration.id

    finally:
        connection.close()


def test_administration_context_rejects_cross_tenant_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(
            connection,
            tenant_id="tenant-001",
        )
        administration = seed_administration(
            connection,
            tenant_id="tenant-002",
        )
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is None

    finally:
        connection.close()


def test_administration_context_rejects_missing_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=999999,
        )

        assert context is None

    finally:
        connection.close()


def test_administration_context_rejects_inactive_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)
        administration = seed_administration(
            connection,
            status="inactive",
        )
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is None

    finally:
        connection.close()


def test_administration_context_rejects_inactive_user():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(
            connection,
            status="inactive",
        )
        administration = seed_administration(connection)
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is None

    finally:
        connection.close()


def test_administration_context_does_not_grant_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)
        administration = seed_administration(connection)
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is not None

        authority = connection.execute(
            """
            SELECT *
            FROM administration_authorities
            WHERE user_id = ?
              AND administration_id = ?
            """,
            (
                user_id,
                administration.id,
            ),
        ).fetchone()

        assert authority is None

    finally:
        connection.close()


def test_administration_context_does_not_use_application_role_as_authority():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)
        administration = seed_administration(connection)
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
        )

        assert context is not None

        user = connection.execute(
            """
            SELECT role
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        assert user["role"] == "teacher"

        authority = connection.execute(
            """
            SELECT *
            FROM administration_authorities
            WHERE user_id = ?
              AND administration_id = ?
            """,
            (
                user_id,
                administration.id,
            ),
        ).fetchone()

        assert authority is None

    finally:
        connection.close()


def test_tenant_does_not_silently_select_an_administration():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(connection)

        first = seed_administration(
            connection,
            tenant_id="tenant-001",
        )
        second = seed_administration(
            connection,
            tenant_id="tenant-001",
        )

        service = AdministrationContextService(connection)

        first_context = service.resolve(
            user_id=user_id,
            administration_id=first.id,
        )
        second_context = service.resolve(
            user_id=user_id,
            administration_id=second.id,
        )

        assert first.id != second.id
        assert first_context is not None
        assert second_context is not None
        assert first_context.administration_id == first.id
        assert second_context.administration_id == second.id

    finally:
        connection.close()


def test_supplied_tenant_must_not_override_authenticated_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(
            connection,
            tenant_id="tenant-001",
        )
        administration = seed_administration(
            connection,
            tenant_id="tenant-001",
        )
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
            tenant_id="tenant-002",
        )

        assert context is None

    finally:
        connection.close()


def test_matching_supplied_tenant_confirms_authenticated_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_tables(connection)

    try:
        user_id = seed_user(
            connection,
            tenant_id="tenant-001",
        )
        administration = seed_administration(
            connection,
            tenant_id="tenant-001",
        )
        service = AdministrationContextService(connection)

        context = service.resolve(
            user_id=user_id,
            administration_id=administration.id,
            tenant_id="tenant-001",
        )

        assert context is not None
        assert context.tenant_id == "tenant-001"
        assert context.administration_id == administration.id

    finally:
        connection.close()
