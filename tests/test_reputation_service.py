import logging
import sqlite3

import pytest

from database import get_connection, init_db
from models.service_act import ServiceAct, ServiceActStatus
from repositories.reputation_repository import ReputationRepository
from repositories.service_act_repository import ServiceActRepository
from services.reputation_service import ReputationService


def _setup(tmp_path):
    db_path = tmp_path / "reputation_service.db"
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

    user_ids = []

    for name, role in (
        ("Provider", "member"),
        ("Recipient", "member"),
        ("Other User", "member"),
    ):
        cursor = connection.execute(
            """
            INSERT INTO users (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                name,
                f"{name.lower().replace(' ', '.')}@example.com",
                role,
                "active",
            ),
        )
        user_ids.append(cursor.lastrowid)

    connection.commit()

    service_act_repository = ServiceActRepository(connection)
    reputation_repository = ReputationRepository(connection)

    service = ReputationService(
        reputation_repository,
        service_act_repository,
    )

    return (
        connection,
        service_act_repository,
        reputation_repository,
        service,
        user_ids,
    )


def _completed_act(service_act_repository, provider_id, recipient_id):
    act = ServiceAct(
        id=None,
        tenant_id="tenant-001",
        provider_user_id=provider_id,
        recipient_user_id=recipient_id,
        title="Completed Service",
        description="A successfully completed service.",
        status=ServiceActStatus.COMPLETED,
    )
    return service_act_repository.create(act)


def test_recipient_can_submit_reputation(tmp_path):
    (
        connection,
        service_act_repository,
        reputation_repository,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    event = service.submit(
        tenant_id="tenant-001",
        service_act_id=act.id,
        reviewer_user_id=recipient_id,
        score=5,
        comment="Excellent service.",
    )

    assert event.id is not None
    assert event.tenant_id == "tenant-001"
    assert event.service_act_id == act.id
    assert event.subject_user_id == provider_id
    assert event.reviewer_user_id == recipient_id
    assert event.score == 5
    assert event.comment == "Excellent service."

    connection.close()


def test_reputation_cannot_be_submitted_before_completion(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = ServiceAct(
        id=None,
        tenant_id="tenant-001",
        provider_user_id=provider_id,
        recipient_user_id=recipient_id,
        title="Incomplete Service",
        description="Not completed yet.",
        status=ServiceActStatus.SUBMITTED,
    )

    act = service_act_repository.create(act)

    with pytest.raises(ValueError, match="completed Service Acts"):
        service.submit(
            "tenant-001",
            act.id,
            recipient_id,
            5,
        )

    connection.close()


def test_only_recipient_can_submit_reputation(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, other_id = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(ValueError, match="recipient"):
        service.submit(
            "tenant-001",
            act.id,
            other_id,
            5,
        )

    connection.close()


@pytest.mark.parametrize("score", [0, -1, 6, 10])
def test_invalid_scores_are_rejected(tmp_path, score):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(ValueError, match="between 1 and 5"):
        service.submit(
            "tenant-001",
            act.id,
            recipient_id,
            score,
        )

    connection.close()


def test_non_integer_score_is_rejected(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(ValueError, match="integer"):
        service.submit(
            "tenant-001",
            act.id,
            recipient_id,
            4.5,
        )

    connection.close()


def test_duplicate_reputation_is_rejected(tmp_path):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    service.submit(
        "tenant-001",
        act.id,
        recipient_id,
        5,
    )

    with pytest.raises(ValueError, match="already exists"):
        service.submit(
            "tenant-001",
            act.id,
            recipient_id,
            4,
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

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with pytest.raises(ValueError, match="service act not found"):
        service.submit(
            "tenant-999",
            act.id,
            recipient_id,
            5,
        )

    connection.close()


def test_reputation_audit_event_is_emitted(tmp_path, caplog):
    (
        connection,
        service_act_repository,
        _,
        service,
        ids,
    ) = _setup(tmp_path)

    provider_id, recipient_id, _ = ids

    act = _completed_act(
        service_act_repository,
        provider_id,
        recipient_id,
    )

    with caplog.at_level(
        logging.INFO,
        logger="kosfintech.audit",
    ):
        event = service.submit(
            "tenant-001",
            act.id,
            recipient_id,
            5,
            "Excellent service.",
        )

    assert "reputation_submitted" in caplog.text
    assert str(event.id) in caplog.text
    assert str(act.id) in caplog.text
    assert '"score": 5' in caplog.text

    connection.close()
