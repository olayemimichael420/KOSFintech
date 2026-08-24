import database
import pytest

from models.service_act import ServiceAct, ServiceActStatus
from repositories.service_act_repository import ServiceActRepository
from services.service_act_service import ServiceActService


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_service.db"
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


def _create_act(connection):
    provider = _create_user(
        connection,
        "tenant-a",
        "Provider",
    )
    recipient = _create_user(
        connection,
        "tenant-a",
        "Recipient",
    )

    repository = ServiceActRepository(connection)

    act = repository.create(
        ServiceAct(
            id=None,
            tenant_id="tenant-a",
            provider_user_id=provider,
            recipient_user_id=recipient,
            title="Tutoring",
            description="Mathematics tutoring.",
        )
    )

    return repository, act


def test_complete_service_act_through_valid_lifecycle(
    tmp_path,
    monkeypatch,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.ACCEPTED,
    )
    assert act.status == ServiceActStatus.ACCEPTED
    assert act.accepted_at is not None

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.IN_PROGRESS,
    )
    assert act.status == ServiceActStatus.IN_PROGRESS
    assert act.started_at is not None

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.SUBMITTED,
    )
    assert act.status == ServiceActStatus.SUBMITTED
    assert act.submitted_at is not None

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.COMPLETED,
    )
    assert act.status == ServiceActStatus.COMPLETED
    assert act.completed_at is not None


@pytest.mark.parametrize(
    "target_status",
    [
        ServiceActStatus.COMPLETED,
        ServiceActStatus.IN_PROGRESS,
        ServiceActStatus.SUBMITTED,
    ],
)
def test_invalid_direct_transitions_from_created_are_rejected(
    tmp_path,
    monkeypatch,
    target_status,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    with pytest.raises(ValueError, match="invalid service act transition"):
        service.transition(
            "tenant-a",
            act.id,
            target_status,
        )


def test_completed_act_cannot_transition_again(
    tmp_path,
    monkeypatch,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    for status in (
        ServiceActStatus.ACCEPTED,
        ServiceActStatus.IN_PROGRESS,
        ServiceActStatus.SUBMITTED,
        ServiceActStatus.COMPLETED,
    ):
        act = service.transition(
            "tenant-a",
            act.id,
            status,
        )

    with pytest.raises(ValueError, match="invalid service act transition"):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.CANCELLED,
            cancellation_reason="Too late",
        )


def test_cancellation_requires_reason(
    tmp_path,
    monkeypatch,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    with pytest.raises(
        ValueError,
        match="cancellation reason is required",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.CANCELLED,
        )


def test_cancellation_records_reason_and_timestamp(
    tmp_path,
    monkeypatch,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.CANCELLED,
        cancellation_reason="Recipient cancelled the request.",
    )

    assert act.status == ServiceActStatus.CANCELLED
    assert act.cancelled_at is not None
    assert (
        act.cancellation_reason
        == "Recipient cancelled the request."
    )


def test_service_act_transition_is_tenant_scoped(
    tmp_path,
    monkeypatch,
):
    repository, act = _create_act(
        _setup_fresh_db(tmp_path, monkeypatch)
    )

    service = ServiceActService(repository)

    with pytest.raises(ValueError, match="service act not found"):
        service.transition(
            "tenant-b",
            act.id,
            ServiceActStatus.ACCEPTED,
        )
