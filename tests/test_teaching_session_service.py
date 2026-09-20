import sqlite3

import pytest

from models.teaching_session import TeachingSession
from repositories.teaching_session_repository import TeachingSessionRepository
from services.teaching_session_service import TeachingSessionService


def _create_service(tenant_id="tenant-1", connection=None):
    if connection is None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

        connection.execute(
            """
            CREATE TABLE teaching_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                UNIQUE (tenant_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX ux_teaching_sessions_id_tenant
            ON teaching_sessions(id, tenant_id)
            """
        )
        connection.commit()

    repository = TeachingSessionRepository(connection)

    return (
        TeachingSessionService(
            repository=repository,
            tenant_id=tenant_id,
        ),
        connection,
    )


def test_create_rejects_tenant_mismatch():
    service, _ = _create_service()

    session = TeachingSession(
        id=None,
        tenant_id="tenant-2",
        name="2026 Teaching Session",
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(session)


def test_create_rejects_invalid_date_range():
    service, _ = _create_service()

    session = TeachingSession(
        id=None,
        tenant_id="tenant-1",
        name="2026 Teaching Session",
        start_date="2027-01-01",
        end_date="2026-12-31",
    )

    with pytest.raises(
        ValueError,
        match="start date must not be after end date",
    ):
        service.create(session)


def test_create_delegates_valid_session():
    service, _ = _create_service()

    session = TeachingSession(
        id=None,
        tenant_id="tenant-1",
        name="2026 Teaching Session",
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    created = service.create(session)

    assert created.id is not None
    assert created.tenant_id == "tenant-1"
    assert created.name == "2026 Teaching Session"


def test_list_is_tenant_scoped():
    service, connection = _create_service()

    other_service, _ = _create_service(
        tenant_id="tenant-2",
        connection=connection,
    )

    service.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="Session A",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    other_service.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-2",
            name="Session B",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    sessions = service.list()

    assert len(sessions) == 1
    assert sessions[0].tenant_id == "tenant-1"


def test_get_is_tenant_scoped():
    service, connection = _create_service()

    other_service, _ = _create_service(
        tenant_id="tenant-2",
        connection=connection,
    )

    session = other_service.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-2",
            name="Session B",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    assert service.get(session.id) is None

def test_create_requires_write_permission():
    import database
    from models.permission import Permission
    from models.role import Role
    from models.role_permission import RolePermissionLink
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.role_permission_repository import RolePermissionRepository
    from repositories.role_repository import RoleRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = database.get_connection()
    try:
        tenant_id = "tenant-auth"
        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                "Teaching User",
                "teaching@test",
                "member",
                "active",
            ),
        )
        user_id = cursor.lastrowid

        role = RoleRepository(connection).create(
            Role(None, tenant_id, "teacher", "Teacher")
        )

        PermissionRepository(connection).create(
            Permission(
                None,
                tenant_id,
                "teaching_session.write",
                "Create teaching sessions",
            )
        )

        UserRoleRepository(connection).create(
            UserRoleLink(tenant_id, user_id, role.id)
        )

        service = TeachingSessionService(
            repository=TeachingSessionRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(
            PermissionError,
            match="teaching_session.write",
        ):
            service.create(
                TeachingSession(
                    id=None,
                    tenant_id=tenant_id,
                    name="2026 Teaching Session",
                    start_date="2026-01-01",
                    end_date="2026-12-31",
                )
            )
    finally:
        connection.close()


def test_list_requires_read_permission():
    import database
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.role_repository import RoleRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = database.get_connection()
    try:
        tenant_id = "tenant-auth"
        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                "Teaching User",
                "teaching-list@test",
                "member",
                "active",
            ),
        )
        user_id = cursor.lastrowid

        role = RoleRepository(connection).create(
            Role(None, tenant_id, "teacher", "Teacher")
        )

        PermissionRepository(connection).create(
            Permission(
                None,
                tenant_id,
                "teaching_session.write",
                "Create teaching sessions",
            )
        )

        UserRoleRepository(connection).create(
            UserRoleLink(tenant_id, user_id, role.id)
        )

        service = TeachingSessionService(
            repository=TeachingSessionRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(
            PermissionError,
            match="teaching_session.read",
        ):
            service.list()
    finally:
        connection.close()


def test_get_requires_read_permission():
    import database
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.role_repository import RoleRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = database.get_connection()
    try:
        tenant_id = "tenant-auth"
        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                "Teaching User",
                "teaching-get@test",
                "member",
                "active",
            ),
        )
        user_id = cursor.lastrowid

        role = RoleRepository(connection).create(
            Role(None, tenant_id, "teacher", "Teacher")
        )

        PermissionRepository(connection).create(
            Permission(
                None,
                tenant_id,
                "teaching_session.write",
                "Create teaching sessions",
            )
        )

        UserRoleRepository(connection).create(
            UserRoleLink(tenant_id, user_id, role.id)
        )

        service = TeachingSessionService(
            repository=TeachingSessionRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(
            PermissionError,
            match="teaching_session.read",
        ):
            service.get(1)
    finally:
        connection.close()
