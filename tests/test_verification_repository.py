import sqlite3

import database
import pytest

from models.service_act import ServiceAct, ServiceActStatus
from models.verification import Verification, VerificationDecision
from repositories.service_act_repository import ServiceActRepository
from repositories.verification_repository import VerificationRepository


def _setup(tmp_path, monkeypatch):
    db_path = tmp_path / "verification_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "Provider", "member"),
    )
    provider_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "Recipient", "member"),
    )
    recipient_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "Verifier", "member"),
    )
    verifier_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.commit()

    act = ServiceAct(
        id=None,
        tenant_id="tenant-001",
        provider_user_id=provider_id,
        recipient_user_id=recipient_id,
        title="Test service",
        description="Test service description",
        status=ServiceActStatus.CREATED,
    )

    act = ServiceActRepository(connection).create(act)

    return connection, act, verifier_id


def test_create_and_get(tmp_path, monkeypatch):
    connection, act, verifier_id = _setup(tmp_path, monkeypatch)

    try:
        repository = VerificationRepository(connection)

        verification = Verification(
            id=None,
            tenant_id="tenant-001",
            service_act_id=act.id,
            verifier_user_id=verifier_id,
            decision=VerificationDecision.APPROVED,
        )

        created = repository.create(verification)
        loaded = repository.get("tenant-001", created.id)

        assert loaded is not None
        assert loaded.service_act_id == act.id
        assert loaded.verifier_user_id == verifier_id
        assert loaded.decision == VerificationDecision.APPROVED
    finally:
        connection.close()


def test_list_by_act(tmp_path, monkeypatch):
    connection, act, verifier_id = _setup(tmp_path, monkeypatch)

    try:
        repository = VerificationRepository(connection)

        repository.create(
            Verification(
                id=None,
                tenant_id="tenant-001",
                service_act_id=act.id,
                verifier_user_id=verifier_id,
                decision=VerificationDecision.APPROVED,
            )
        )

        results = repository.list_by_act("tenant-001", act.id)

        assert len(results) == 1
        assert results[0].service_act_id == act.id
    finally:
        connection.close()


def test_duplicate_verifier_is_rejected(tmp_path, monkeypatch):
    connection, act, verifier_id = _setup(tmp_path, monkeypatch)

    try:
        repository = VerificationRepository(connection)

        verification = Verification(
            id=None,
            tenant_id="tenant-001",
            service_act_id=act.id,
            verifier_user_id=verifier_id,
            decision=VerificationDecision.APPROVED,
        )

        repository.create(verification)

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(
                Verification(
                    id=None,
                    tenant_id="tenant-001",
                    service_act_id=act.id,
                    verifier_user_id=verifier_id,
                    decision=VerificationDecision.REJECTED,
                )
            )
    finally:
        connection.close()
