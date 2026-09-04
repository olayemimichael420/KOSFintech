import sqlite3

import database
import pytest

from models.service_act import ServiceAct
from repositories.service_act_repository import ServiceActRepository
from services.service_act_service import ServiceActService
from services.permission_resolution_service import PermissionResolutionService


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_tenant_isolation.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()


def _create_user(connection, tenant_id, name):
    cursor = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, name, "member"),
    )
    connection.commit()
    return cursor.lastrowid


def test_cross_tenant_provider_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-a",
            "Provider A",
        )
        recipient = _create_user(
            connection,
            "tenant-b",
            "Recipient B",
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO service_acts (
                    tenant_id,
                    provider_user_id,
                    recipient_user_id,
                    title,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "tenant-b",
                    provider,
                    recipient,
                    "Cross Tenant Act",
                    "Should be rejected",
                ),
            )
    finally:
        connection.close()


def test_cross_tenant_recipient_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-a",
            "Provider A",
        )
        recipient = _create_user(
            connection,
            "tenant-b",
            "Recipient B",
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO service_acts (
                    tenant_id,
                    provider_user_id,
                    recipient_user_id,
                    title,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "tenant-a",
                    provider,
                    recipient,
                    "Cross Tenant Act",
                    "Should be rejected",
                ),
            )
    finally:
        connection.close()


def test_repository_lists_only_requested_tenant(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider_a = _create_user(
            connection,
            "tenant-a",
            "Provider A",
        )
        recipient_a = _create_user(
            connection,
            "tenant-a",
            "Recipient A",
        )

        provider_b = _create_user(
            connection,
            "tenant-b",
            "Provider B",
        )
        recipient_b = _create_user(
            connection,
            "tenant-b",
            "Recipient B",
        )

        repository = ServiceActRepository(connection)

        repository.create(
            ServiceAct(
                id=None,
                tenant_id="tenant-a",
                provider_user_id=provider_a,
                recipient_user_id=recipient_a,
                title="Tenant A Act",
                description="Tenant A service",
            )
        )

        repository.create(
            ServiceAct(
                id=None,
                tenant_id="tenant-b",
                provider_user_id=provider_b,
                recipient_user_id=recipient_b,
                title="Tenant B Act",
                description="Tenant B service",
            )
        )

        tenant_a_acts = repository.list_by_tenant("tenant-a")
        tenant_b_acts = repository.list_by_tenant("tenant-b")

        assert len(tenant_a_acts) == 1
        assert tenant_a_acts[0].title == "Tenant A Act"

        assert len(tenant_b_acts) == 1
        assert tenant_b_acts[0].title == "Tenant B Act"
    finally:
        connection.close()


def test_service_cannot_transition_act_from_another_tenant(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-a",
            "Provider A",
        )
        recipient = _create_user(
            connection,
            "tenant-a",
            "Recipient A",
        )

        repository = ServiceActRepository(connection)

        act = repository.create(
            ServiceAct(
                id=None,
                tenant_id="tenant-a",
                provider_user_id=provider,
                recipient_user_id=recipient,
                title="Tenant A Act",
                description="Tenant A service",
            )
        )

        tenant_b_actor = _create_user(
            connection,
            "tenant-b",
            "Tenant B Actor",
        )

        connection.execute(
            """
            INSERT INTO permissions (tenant_id, name, status)
            VALUES (?, 'service_act.write', 'active')
            """,
            ("tenant-b",),
        )
        permission_id = connection.execute(
            """
            SELECT id
            FROM permissions
            WHERE tenant_id = ?
              AND name = 'service_act.write'
            ORDER BY id DESC
            LIMIT 1
            """,
            ("tenant-b",),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO roles (tenant_id, name, status)
            VALUES (?, ?, 'active')
            """,
            ("tenant-b", f"service-act-{tenant_b_actor}"),
        )
        role_id = connection.execute(
            """
            SELECT id
            FROM roles
            WHERE tenant_id = ?
              AND name = ?
            """,
            ("tenant-b", f"service-act-{tenant_b_actor}"),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            """,
            ("tenant-b", tenant_b_actor, role_id),
        )

        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id,
                role_id,
                permission_id
            )
            VALUES (?, ?, ?)
            """,
            ("tenant-b", role_id, permission_id),
        )
        connection.commit()

        permission_service = PermissionResolutionService(connection)
        service = ServiceActService(
            repository,
            permission_service,
        )

        with pytest.raises(
            ValueError,
            match="service act not found",
        ):
            service.transition(
                "tenant-b",
                act.id,
                "accepted",
                actor_id=tenant_b_actor,
            )
    finally:
        connection.close()
