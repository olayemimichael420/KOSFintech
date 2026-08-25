import logging
import sqlite3

import pytest

from database import init_db
from models.dispute import (
    DisputeResolution,
    DisputeStatus,
)
from models.service_act import ServiceAct, ServiceActStatus
from repositories.dispute_repository import DisputeRepository
from repositories.service_act_repository import ServiceActRepository
from services.dispute_service import DisputeService


def _setup(tmp_path):
    db_path = tmp_path / "dispute_service.db"

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    import config

    original_db_file = config.settings.db_file

    object.__setattr__(
        config.settings,
        "db_file",
        db_path,
    )

    try:
        init_db()
    finally:
        object.__setattr__(
            config.settings,
            "db_file",
            original_db_file,
        )
        connection.close()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    users = []

    for name in (
        "Provider",
        "Recipient",
        "Other User",
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
                "tenant-001",
                name,
                f"{name.lower().replace(' ', '.')}@example.com",
                "member",
                "active",
            ),
        )
        users.append(cursor.lastrowid)

    connection.commit()

    service_act_repository = ServiceActRepository(connection)
    dispute_repository = DisputeRepository(connection)

    service = DisputeService(
        dispute_repository,
        service_act_repository,
    )

    return (
        connection,
        service_act_repository,
        dispute_repository,
        service,
        users,
    )


def _create_act(
    service_act_repository,
    provider_id,
    recipient_id,
):
    return service_act_repository.create(
        ServiceAct(
            id=None,
            tenant_id="tenant-001",
            provider_user_id=provider_id,
            recipient_user_id=recipient_id,
            title="Completed Service",
            description="Service involved in dispute testing.",
            status=ServiceActStatus.COMPLETED,
        )
    )


def test_provider_can_open_dispute(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        tenant_id="tenant-001",
        service_act_id=act.id,
        initiator_user_id=provider_id,
        reason="The agreed service conditions were not fulfilled.",
    )

    assert dispute.id is not None
    assert dispute.tenant_id == "tenant-001"
    assert dispute.service_act_id == act.id
    assert dispute.initiator_user_id == provider_id
    assert dispute.status == DisputeStatus.OPEN
    assert dispute.initiator_role.value == "provider"

    connection.close()


def test_recipient_can_open_dispute(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        recipient_id,
        "The delivered service did not match the agreement.",
    )

    assert dispute.initiator_user_id == recipient_id
    assert dispute.initiator_role.value == "recipient"

    connection.close()


def test_non_participant_cannot_open_dispute(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, other_id = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(
        ValueError,
        match="provider or recipient",
    ):
        service.open_dispute(
            "tenant-001",
            act.id,
            other_id,
            "Invalid dispute attempt.",
        )

    connection.close()


def test_empty_dispute_reason_is_rejected(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(
        ValueError,
        match="dispute reason is required",
    ):
        service.open_dispute(
            "tenant-001",
            act.id,
            provider_id,
            "   ",
        )

    connection.close()


def test_unknown_service_act_cannot_have_dispute(tmp_path):
    (
        connection,
        _,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, _, _ = ids

    with pytest.raises(
        ValueError,
        match="service act not found",
    ):
        service.open_dispute(
            "tenant-001",
            999999,
            provider_id,
            "Unknown Service Act.",
        )

    connection.close()


def test_tenant_boundary_hides_service_act(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(
        ValueError,
        match="service act not found",
    ):
        service.open_dispute(
            "tenant-999",
            act.id,
            provider_id,
            "Cross-tenant dispute attempt.",
        )

    connection.close()


def test_dispute_can_move_to_review(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    reviewed = service.move_to_review(
        "tenant-001",
        dispute.id,
        recipient_id,
    )

    assert reviewed.status == DisputeStatus.UNDER_REVIEW

    connection.close()


def test_only_open_dispute_can_move_to_review(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    service.move_to_review(
        "tenant-001",
        dispute.id,
        recipient_id,
    )

    with pytest.raises(
        ValueError,
        match="only open disputes",
    ):
        service.move_to_review(
            "tenant-001",
            dispute.id,
            recipient_id,
        )

    connection.close()


def test_dispute_can_be_resolved(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        recipient_id,
        "Service disagreement.",
    )

    service.move_to_review(
        "tenant-001",
        dispute.id,
        provider_id,
    )

    resolved = service.resolve(
        tenant_id="tenant-001",
        dispute_id=dispute.id,
        resolved_by_user_id=provider_id,
        resolution=DisputeResolution.RECIPIENT_FAVORED,
        resolution_reason="The recipient's evidence was sufficient.",
    )

    assert resolved.status == DisputeStatus.RESOLVED
    assert resolved.resolution == DisputeResolution.RECIPIENT_FAVORED
    assert resolved.resolution_reason == (
        "The recipient's evidence was sufficient."
    )
    assert resolved.resolved_by_user_id == provider_id
    assert resolved.resolved_at is not None

    connection.close()


def test_resolution_requires_reason(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    service.move_to_review(
        "tenant-001",
        dispute.id,
        recipient_id,
    )

    with pytest.raises(
        ValueError,
        match="resolution reason is required",
    ):
        service.resolve(
            "tenant-001",
            dispute.id,
            provider_id,
            DisputeResolution.NO_FAULT,
            "   ",
        )

    connection.close()


def test_resolution_requires_under_review_status(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    with pytest.raises(
        ValueError,
        match="under review",
    ):
        service.resolve(
            "tenant-001",
            dispute.id,
            recipient_id,
            DisputeResolution.NO_FAULT,
            "No fault established.",
        )

    connection.close()


def test_dispute_can_be_rejected(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    service.move_to_review(
        "tenant-001",
        dispute.id,
        recipient_id,
    )

    rejected = service.reject(
        "tenant-001",
        dispute.id,
        recipient_id,
        "The evidence did not substantiate the claim.",
    )

    assert rejected.status == DisputeStatus.REJECTED
    assert rejected.resolution is None
    assert rejected.resolution_reason == (
        "The evidence did not substantiate the claim."
    )
    assert rejected.resolved_by_user_id == recipient_id
    assert rejected.resolved_at is not None

    connection.close()


def test_dispute_initiator_can_withdraw_open_dispute(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    withdrawn = service.withdraw(
        "tenant-001",
        dispute.id,
        provider_id,
        "The matter has been settled privately.",
    )

    assert withdrawn.status == DisputeStatus.WITHDRAWN
    assert withdrawn.resolution_reason == (
        "The matter has been settled privately."
    )

    connection.close()


def test_non_initiator_cannot_withdraw_dispute(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    with pytest.raises(
        ValueError,
        match="only the dispute initiator",
    ):
        service.withdraw(
            "tenant-001",
            dispute.id,
            recipient_id,
            "Attempted unauthorized withdrawal.",
        )

    connection.close()


def test_withdrawn_dispute_cannot_be_resolved(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    service.withdraw(
        "tenant-001",
        dispute.id,
        provider_id,
        "Matter settled.",
    )

    with pytest.raises(
        ValueError,
        match="under review",
    ):
        service.resolve(
            "tenant-001",
            dispute.id,
            provider_id,
            DisputeResolution.NO_FAULT,
            "Attempted resolution.",
        )

    connection.close()


def test_dispute_audit_events_are_emitted(tmp_path, caplog):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with caplog.at_level(
        logging.INFO,
        logger="kosfintech.audit",
    ):
        dispute = service.open_dispute(
            "tenant-001",
            act.id,
            provider_id,
            "Service disagreement.",
        )

        service.move_to_review(
            "tenant-001",
            dispute.id,
            recipient_id,
        )

        service.resolve(
            "tenant-001",
            dispute.id,
            recipient_id,
            DisputeResolution.MUTUAL_SETTLEMENT,
            "Both parties agreed to settle.",
        )

    assert "dispute_opened" in caplog.text
    assert "dispute_under_review" in caplog.text
    assert "dispute_resolved" in caplog.text
    assert str(dispute.id) in caplog.text

    connection.close()


def test_dispute_operations_are_tenant_scoped(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _create_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    dispute = service.open_dispute(
        "tenant-001",
        act.id,
        provider_id,
        "Service disagreement.",
    )

    with pytest.raises(
        ValueError,
        match="dispute not found",
    ):
        service.move_to_review(
            "tenant-999",
            dispute.id,
            recipient_id,
        )

    connection.close()
