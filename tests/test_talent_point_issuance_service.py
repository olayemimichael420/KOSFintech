import pytest

import database
from models.service_act import ServiceAct, ServiceActStatus
from models.talent_point import TalentPointTransaction
from repositories.service_act_repository import ServiceActRepository
from repositories.talent_point_repository import TalentPointRepository
from services.talent_point_issuance_service import TalentPointIssuanceService


def _setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "talent_point_issuance.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

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


def _create_act(
    connection,
    tenant_id,
    provider_id,
    recipient_id,
    status=ServiceActStatus.COMPLETED,
):
    repository = ServiceActRepository(connection)

    return repository.create(
        ServiceAct(
            id=None,
            tenant_id=tenant_id,
            provider_user_id=provider_id,
            recipient_user_id=recipient_id,
            title="Completed Service",
            description="Verified service act",
            status=status,
        )
    )


def _create_completed_acts(
    connection,
    tenant_id,
    provider_id,
    recipient_id,
    count,
):
    acts = []

    for index in range(count):
        acts.append(
            _create_act(
                connection,
                tenant_id,
                provider_id,
                recipient_id,
            )
        )

    return acts


def test_completed_service_act_can_receive_tp(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        transaction = service.issue_for_service_act(
            tenant_id="tenant-1",
            service_act=act,
            amount=100,
            reference="service-act-reward",
        )

        assert transaction.id is not None
        assert transaction.tenant_id == "tenant-1"
        assert transaction.user_id == provider
        assert transaction.service_act_id == act.id
        assert transaction.amount == 100
        assert transaction.transaction_type == "issuance"

    finally:
        connection.close()


def test_incomplete_service_act_cannot_receive_tp(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
            ServiceActStatus.SUBMITTED,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="completed",
        ):
            service.issue_for_service_act(
                "tenant-1",
                act,
                100,
            )

    finally:
        connection.close()


def test_cancelled_service_act_cannot_receive_tp(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
            ServiceActStatus.CANCELLED,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="completed",
        ):
            service.issue_for_service_act(
                "tenant-1",
                act,
                100,
            )

    finally:
        connection.close()


def test_duplicate_issuance_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        service.issue_for_service_act(
            "tenant-1",
            act,
            100,
        )

        with pytest.raises(
            ValueError,
            match="already",
        ):
            service.issue_for_service_act(
                "tenant-1",
                act,
                100,
            )

    finally:
        connection.close()


def test_invalid_zero_amount_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="greater than zero",
        ):
            service.issue_for_service_act(
                "tenant-1",
                act,
                0,
            )

    finally:
        connection.close()


def test_invalid_negative_amount_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="greater than zero",
        ):
            service.issue_for_service_act(
                "tenant-1",
                act,
                -100,
            )

    finally:
        connection.close()


def test_daily_cap_is_enforced(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        acts = _create_completed_acts(
            connection,
            "tenant-1",
            provider,
            recipient,
            6,
        )

        repository = TalentPointRepository(connection)

        # Valid completed Service Acts are used for every
        # pre-existing ledger transaction.
        for act in acts[:5]:
            repository.create(
                TalentPointTransaction(
                    id=None,
                    tenant_id="tenant-1",
                    user_id=provider,
                    service_act_id=act.id,
                    amount=10_000,
                    transaction_type="issuance",
                    reference="existing-issuance",
                )
            )

        service = TalentPointIssuanceService(repository)

        with pytest.raises(
            ValueError,
            match="daily",
        ):
            service.issue_for_service_act(
                "tenant-1",
                acts[5],
                1,
            )

    finally:
        connection.close()


def test_total_supply_cap_is_enforced(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        acts = _create_completed_acts(
            connection,
            "tenant-1",
            provider,
            recipient,
            2,
        )

        repository = TalentPointRepository(connection)

        repository.create(
            TalentPointTransaction(
                id=None,
                tenant_id="tenant-1",
                user_id=provider,
                service_act_id=acts[0].id,
                amount=99_999_900,
                transaction_type="issuance",
                reference="existing-supply",
            )
        )

        service = TalentPointIssuanceService(repository)

        with pytest.raises(
            ValueError,
            match="total",
        ):
            service.issue_for_service_act(
                "tenant-1",
                acts[1],
                101,
            )

    finally:
        connection.close()


def test_tenant_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
):
    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )

        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with pytest.raises(
            ValueError,
            match="tenant",
        ):
            service.issue_for_service_act(
                "tenant-2",
                act,
                100,
            )

    finally:
        connection.close()


def test_tp_issuance_emits_audit_event(tmp_path, monkeypatch, caplog):
    import logging
    import json

    connection = _setup_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(
            connection,
            "tenant-1",
            "Provider",
        )
        recipient = _create_user(
            connection,
            "tenant-1",
            "Recipient",
        )

        act = _create_act(
            connection,
            "tenant-1",
            provider,
            recipient,
        )

        service = TalentPointIssuanceService(
            TalentPointRepository(connection)
        )

        with caplog.at_level(
            logging.INFO,
            logger="kosfintech.audit",
        ):
            transaction = service.issue_for_service_act(
                tenant_id="tenant-1",
                service_act=act,
                amount=100,
                reference="service-act-reward",
            )

        audit_records = [
            record
            for record in caplog.records
            if record.message.startswith("AUDIT ")
        ]

        assert len(audit_records) == 1

        payload = json.loads(
            audit_records[0].message[len("AUDIT "):]
        )

        assert payload["event_type"] == "talent_point_issuance"
        assert payload["actor_id"] == provider
        assert payload["tenant_id"] == "tenant-1"
        assert payload["action"] == "issue_talent_points"

        assert payload["metadata"]["transaction_id"] == transaction.id
        assert payload["metadata"]["service_act_id"] == act.id
        assert payload["metadata"]["user_id"] == provider
        assert payload["metadata"]["amount"] == 100
        assert payload["metadata"]["transaction_type"] == "issuance"
        assert payload["metadata"]["reference"] == "service-act-reward"

    finally:
        connection.close()
