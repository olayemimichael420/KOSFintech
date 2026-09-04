import pytest

import database

from models.service_act import ServiceAct, ServiceActStatus
from models.verification import VerificationDecision
from repositories.service_act_repository import ServiceActRepository
from repositories.verification_repository import VerificationRepository
from services.permission_resolution_service import PermissionResolutionService
from services.verification_service import VerificationService


def _setup(tmp_path, monkeypatch):
    db_path = tmp_path / "verification_service.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    users = [
        ("tenant-001", "Provider", "member"),
        ("tenant-001", "Recipient", "member"),
        ("tenant-001", "Verifier", "member"),
    ]

    for tenant_id, name, role in users:
        connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            (tenant_id, name, role),
        )

    verifier_id = connection.execute(
        """
        SELECT id
        FROM users
        WHERE tenant_id = ? AND name = ?
        """,
        ("tenant-001", "Verifier"),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, 'verification_actor', 'active')
        """,
        ("tenant-001",),
    )

    role_id = connection.execute(
        """
        SELECT id
        FROM roles
        WHERE tenant_id = ? AND name = ?
        """,
        ("tenant-001", "verification_actor"),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, 'verification.write', 'active')
        """,
        ("tenant-001",),
    )

    permission_id = connection.execute(
        """
        SELECT id
        FROM permissions
        WHERE tenant_id = ?
          AND name = 'verification.write'
        ORDER BY id DESC
        LIMIT 1
        """,
        ("tenant-001",),
    ).fetchone()["id"]

    # All three users are authorization-capable actors for this fixture.
    # Domain eligibility is tested separately by VerificationService.
    for user_id in (
        connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
            ORDER BY id
            """,
            ("tenant-001",),
        ).fetchall()
    ):
        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            """,
            ("tenant-001", user_id["id"], role_id),
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
        ("tenant-001", role_id, permission_id),
    )

    connection.commit()

    ids = [
        row["id"]
        for row in connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
            ORDER BY id
            """,
            ("tenant-001",),
        ).fetchall()
    ]

    act = ServiceAct(
        id=None,
        tenant_id="tenant-001",
        provider_user_id=ids[0],
        recipient_user_id=ids[1],
        title="Test service",
        description="Test service description",
        status=ServiceActStatus.SUBMITTED,
    )

    act = ServiceActRepository(connection).create(act)

    verification_repository = VerificationRepository(connection)

    permission_service = PermissionResolutionService(connection)

    service = VerificationService(
        verification_repository,
        ServiceActRepository(connection),
        permission_service,
    )

    return connection, act, ids[2], service


def test_approval_succeeds(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        verification = service.verify(
            "tenant-001",
            act.id,
            verifier_id,
            VerificationDecision.APPROVED,
            actor_user_id=verifier_id,
        )

        assert verification.id is not None
        assert verification.decision == VerificationDecision.APPROVED
        assert verification.reason is None
    finally:
        connection.close()


def test_verification_requires_actor(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with pytest.raises(
            PermissionError,
            match="verification actor is required",
        ):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
            )
    finally:
        connection.close()


def test_verification_actor_cannot_impersonate_verifier(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with pytest.raises(
            PermissionError,
            match="must be the verifier",
        ):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=act.provider_user_id,
            )
    finally:
        connection.close()


def test_rejection_requires_reason(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with pytest.raises(ValueError, match="rejection reason"):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.REJECTED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_rejection_with_reason_succeeds(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        verification = service.verify(
            "tenant-001",
            act.id,
            verifier_id,
            VerificationDecision.REJECTED,
            reason="Service was not completed as described.",
            actor_user_id=verifier_id,
        )

        assert verification.decision == VerificationDecision.REJECTED
        assert verification.reason == (
            "Service was not completed as described."
        )
    finally:
        connection.close()


def test_missing_service_act_fails(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with pytest.raises(ValueError, match="service act not found"):
            service.verify(
                "tenant-001",
                999999,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_same_verifier_cannot_verify_twice(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        service.verify(
            "tenant-001",
            act.id,
            verifier_id,
            VerificationDecision.APPROVED,
            actor_user_id=verifier_id,
        )

        with pytest.raises(
            ValueError,
            match="already verified",
        ):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.REJECTED,
                reason="Second decision",
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_wrong_tenant_cannot_verify_existing_act(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with pytest.raises(PermissionError, match="verification permission denied"):
            service.verify(
                "tenant-002",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_verification_emits_audit_event(
    tmp_path,
    monkeypatch,
    caplog,
):
    import json
    import logging

    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        with caplog.at_level(
            logging.INFO,
            logger="kosfintech.audit",
        ):
            verification = service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )

        records = [
            record
            for record in caplog.records
            if record.name == "kosfintech.audit"
        ]

        assert len(records) == 1

        message = records[0].message
        assert message.startswith("AUDIT ")

        payload = json.loads(message[len("AUDIT "):])

        assert payload["event_type"] == "verification_submitted"
        assert payload["actor_id"] == verifier_id
        assert payload["tenant_id"] == "tenant-001"
        assert payload["action"] == "submit_verification"
        assert payload["metadata"]["verification_id"] == verification.id
        assert payload["metadata"]["service_act_id"] == act.id
        assert payload["metadata"]["decision"] == "approved"
        assert payload["metadata"]["reason"] is None
    finally:
        connection.close()

def test_verification_requires_submitted_service_act(tmp_path, monkeypatch):
    connection, act, verifier_id, service = _setup(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            UPDATE service_acts
            SET status = ?
            WHERE tenant_id = ?
            AND id = ?
            """,
            (
                ServiceActStatus.CREATED.value,
                "tenant-001",
                act.id,
            ),
        )
        connection.commit()

        with pytest.raises(ValueError, match="submitted"):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_provider_cannot_verify_own_service_act(tmp_path, monkeypatch):
    connection, act, _, service = _setup(tmp_path, monkeypatch)
    try:
        provider_id = act.provider_user_id

        with pytest.raises(ValueError, match="cannot verify"):
            service.verify(
                "tenant-001",
                act.id,
                provider_id,
                VerificationDecision.APPROVED,
                actor_user_id=provider_id,
            )
    finally:
        connection.close()


def test_recipient_cannot_verify_own_service_act(tmp_path, monkeypatch):
    connection, act, _, service = _setup(tmp_path, monkeypatch)
    try:
        recipient_id = act.recipient_user_id

        with pytest.raises(ValueError, match="cannot verify"):
            service.verify(
                "tenant-001",
                act.id,
                recipient_id,
                VerificationDecision.APPROVED,
                actor_user_id=recipient_id,
            )
    finally:
        connection.close()


def test_fourth_verifier_is_rejected(tmp_path, monkeypatch):
    db_path = tmp_path / "verification_four_verifiers.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()

    try:
        users = [
            ("Provider", "member"),
            ("Recipient", "member"),
            ("Verifier One", "member"),
            ("Verifier Two", "member"),
            ("Verifier Three", "member"),
            ("Verifier Four", "member"),
        ]

        ids = {}

        for name, role in users:
            cursor = connection.execute(
                """
                INSERT INTO users (tenant_id, name, role)
                VALUES (?, ?, ?)
                """,
                ("tenant-001", name, role),
            )
            ids[name] = cursor.lastrowid

        # Grant verification.write to every potential verifier.
        for name in (
            "Verifier One",
            "Verifier Two",
            "Verifier Three",
            "Verifier Four",
        ):
            user_id = ids[name]

            connection.execute(
                """
                INSERT INTO roles (tenant_id, name, status)
                VALUES (?, ?, 'active')
                """,
                ("tenant-001", f"verification-{user_id}"),
            )

            role_id = connection.execute(
                """
                SELECT id
                FROM roles
                WHERE tenant_id = ? AND name = ?
                """,
                ("tenant-001", f"verification-{user_id}"),
            ).fetchone()["id"]

            connection.execute(
                """
                INSERT INTO permissions (tenant_id, name, status)
                VALUES (?, 'verification.write', 'active')
                """,
                ("tenant-001",),
            )

            permission_id = connection.execute(
                """
                SELECT id
                FROM permissions
                WHERE tenant_id = ?
                  AND name = 'verification.write'
                ORDER BY id DESC
                LIMIT 1
                """,
                ("tenant-001",),
            ).fetchone()["id"]

            connection.execute(
                """
                INSERT INTO user_roles (tenant_id, user_id, role_id)
                VALUES (?, ?, ?)
                """,
                ("tenant-001", user_id, role_id),
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
                ("tenant-001", role_id, permission_id),
            )

        connection.commit()

        act = ServiceActRepository(connection).create(
            ServiceAct(
                id=None,
                tenant_id="tenant-001",
                provider_user_id=ids["Provider"],
                recipient_user_id=ids["Recipient"],
                title="Test service",
                description="Test service description",
                status=ServiceActStatus.SUBMITTED,
            )
        )

        repository = VerificationRepository(connection)
        permission_service = PermissionResolutionService(connection)

        service = VerificationService(
            repository,
            ServiceActRepository(connection),
            permission_service,
        )

        for verifier in (
            "Verifier One",
            "Verifier Two",
            "Verifier Three",
        ):
            service.verify(
                "tenant-001",
                act.id,
                ids[verifier],
                VerificationDecision.APPROVED,
                actor_user_id=ids[verifier],
            )

        with pytest.raises(ValueError, match="maximum"):
            service.verify(
                "tenant-001",
                act.id,
                ids["Verifier Four"],
                VerificationDecision.APPROVED,
                actor_user_id=ids["Verifier Four"],
            )

    finally:
        connection.close()


def test_completed_service_act_cannot_accept_verification(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            UPDATE service_acts
            SET status = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                ServiceActStatus.COMPLETED.value,
                "tenant-001",
                act.id,
            ),
        )
        connection.commit()

        with pytest.raises(ValueError, match="submitted"):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_cancelled_service_act_cannot_accept_verification(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            UPDATE service_acts
            SET status = ?,
                cancellation_reason = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                ServiceActStatus.CANCELLED.value,
                "Cancelled before verification.",
                "tenant-001",
                act.id,
            ),
        )
        connection.commit()

        with pytest.raises(ValueError, match="submitted"):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )
    finally:
        connection.close()


def test_verification_rolls_back_when_audit_persistence_fails(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        def failing_audit_event(*args, **kwargs):
            raise RuntimeError("simulated audit failure")

        monkeypatch.setattr(
            "services.verification_service.audit_event",
            failing_audit_event,
        )

        with pytest.raises(
            RuntimeError,
            match="simulated audit failure",
        ):
            service.verify(
                "tenant-001",
                act.id,
                verifier_id,
                VerificationDecision.APPROVED,
                actor_user_id=verifier_id,
            )

        verification_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM verifications
            WHERE tenant_id = ?
              AND service_act_id = ?
              AND verifier_user_id = ?
            """,
            (
                "tenant-001",
                act.id,
                verifier_id,
            ),
        ).fetchone()[0]

        assert verification_count == 0

    finally:
        connection.close()


def test_verification_persists_audit_event_atomically(
    tmp_path,
    monkeypatch,
):
    connection, act, verifier_id, service = _setup(
        tmp_path,
        monkeypatch,
    )

    try:
        verification = service.verify(
            "tenant-001",
            act.id,
            verifier_id,
            VerificationDecision.APPROVED,
            actor_user_id=verifier_id,
        )

        audit_rows = connection.execute(
            """
            SELECT
                event_type,
                actor_id,
                tenant_id,
                action,
                metadata
            FROM audit_events
            WHERE tenant_id = ?
              AND event_type = ?
            ORDER BY id
            """,
            (
                "tenant-001",
                "verification_submitted",
            ),
        ).fetchall()

        assert len(audit_rows) == 1

        row = audit_rows[0]

        assert row["actor_id"] == verifier_id
        assert row["tenant_id"] == "tenant-001"
        assert row["action"] == "submit_verification"

    finally:
        connection.close()
