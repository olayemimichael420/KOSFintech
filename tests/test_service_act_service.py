import database
import pytest

from models.service_act import ServiceAct, ServiceActStatus
from models.service_request import ServiceRequest, ServiceRequestStatus
from repositories.service_request_repository import ServiceRequestRepository
from repositories.service_act_repository import ServiceActRepository
from services.permission_resolution_service import PermissionResolutionService
from services.service_act_service import ServiceActService


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_service.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()


def _create_user(connection, tenant_id, name, with_permission=True):
    cursor = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, name, "member"),
    )
    user_id = cursor.lastrowid

    if with_permission:
        role_name = f"service-act-{user_id}"

        connection.execute(
            """
            INSERT INTO roles (tenant_id, name, status)
            VALUES (?, ?, 'active')
            """,
            (tenant_id, role_name),
        )

        role_id = connection.execute(
            """
            SELECT id
            FROM roles
            WHERE tenant_id = ?
              AND name = ?
            """,
            (tenant_id, role_name),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO permissions (tenant_id, name, status)
            VALUES (?, 'service_act.write', 'active')
            """,
            (tenant_id,),
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
            (tenant_id,),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            """,
            (tenant_id, user_id, role_id),
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
            (tenant_id, role_id, permission_id),
        )

    connection.commit()
    return user_id


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

    return repository, act, provider, recipient


def _service(connection, repository):
    permission_service = PermissionResolutionService(connection)
    return ServiceActService(
        repository,
        permission_service,
    )


def _create_authorized_request(connection, recipient):
    requester = _create_user(connection, "tenant-a", "Requester")
    repository = ServiceRequestRepository(connection)
    request = repository.create(
        ServiceRequest(
            id=None,
            tenant_id="tenant-a",
            requester_user_id=requester,
            recipient_user_id=recipient,
            title="Tutoring",
            description="Mathematics tutoring.",
            status=ServiceRequestStatus.AUTHORIZED,
        )
    )
    return request, requester


def test_create_service_act_from_authorized_request(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    provider = _create_user(connection, "tenant-a", "Provider")
    request, _ = _create_authorized_request(connection, recipient)
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    created = service.create(
        request,
        provider_user_id=provider,
        actor_id=provider,
    )

    assert created.id is not None
    assert created.tenant_id == "tenant-a"
    assert created.provider_user_id == provider
    assert created.recipient_user_id == recipient
    assert created.title == request.title
    assert created.description == request.description
    assert created.status == ServiceActStatus.CREATED


def test_create_service_act_requires_authorized_request(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    provider = _create_user(connection, "tenant-a", "Provider")
    requester = _create_user(connection, "tenant-a", "Requester")
    request = ServiceRequest(
        id=None,
        tenant_id="tenant-a",
        requester_user_id=requester,
        recipient_user_id=recipient,
        title="Tutoring",
        description="Mathematics tutoring.",
    )
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    with pytest.raises(ValueError, match="must be authorized"):
        service.create(
            request,
            provider_user_id=provider,
            actor_id=provider,
        )


def test_create_service_act_requires_actor(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    provider = _create_user(connection, "tenant-a", "Provider")
    request, _ = _create_authorized_request(connection, recipient)
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    with pytest.raises(PermissionError, match="actor is required"):
        service.create(
            request,
            provider_user_id=provider,
        )


def test_create_service_act_requires_write_permission(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    provider = _create_user(
        connection,
        "tenant-a",
        "Provider",
        with_permission=False,
    )
    request, _ = _create_authorized_request(connection, recipient)
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    with pytest.raises(PermissionError, match="permission denied"):
        service.create(
            request,
            provider_user_id=provider,
            actor_id=provider,
        )


def test_create_service_act_provider_must_differ_from_recipient(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    request, _ = _create_authorized_request(connection, recipient)
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    with pytest.raises(ValueError, match="provider and recipient must differ"):
        service.create(
            request,
            provider_user_id=recipient,
            actor_id=recipient,
        )


def test_create_service_act_rolls_back_when_audit_fails(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    recipient = _create_user(connection, "tenant-a", "Recipient")
    provider = _create_user(connection, "tenant-a", "Provider")
    request, _ = _create_authorized_request(connection, recipient)
    repository = ServiceActRepository(connection)
    service = _service(connection, repository)

    def fail_audit(**kwargs):
        raise RuntimeError("audit failure")

    monkeypatch.setattr(
        "services.service_act_service.audit_event",
        fail_audit,
    )

    with pytest.raises(RuntimeError, match="audit failure"):
        service.create(
            request,
            provider_user_id=provider,
            actor_id=provider,
        )

    assert repository.list_by_tenant("tenant-a") == []


def test_complete_service_act_through_valid_lifecycle(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.ACCEPTED,
        actor_id=recipient,
    )
    assert act.status == ServiceActStatus.ACCEPTED
    assert act.accepted_at is not None

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.IN_PROGRESS,
        actor_id=provider,
    )
    assert act.status == ServiceActStatus.IN_PROGRESS
    assert act.started_at is not None

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.SUBMITTED,
        actor_id=provider,
    )
    assert act.status == ServiceActStatus.SUBMITTED
    assert act.submitted_at is not None


@pytest.mark.parametrize(
    "target_status, actor_role",
    [
        (ServiceActStatus.IN_PROGRESS, "provider"),
        (ServiceActStatus.SUBMITTED, "provider"),
    ],
)
def test_invalid_direct_transitions_from_created_are_rejected(
    tmp_path,
    monkeypatch,
    target_status,
    actor_role,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    actor_id = (
        provider
        if actor_role == "provider"
        else recipient
    )

    with pytest.raises(
        ValueError,
        match="invalid service act transition",
    ):
        service.transition(
            "tenant-a",
            act.id,
            target_status,
            actor_id=actor_id,
        )


def test_completed_act_cannot_transition_again(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    for status, actor_id in (
        (ServiceActStatus.ACCEPTED, recipient),
        (ServiceActStatus.IN_PROGRESS, provider),
        (ServiceActStatus.SUBMITTED, provider),
    ):
        act = service.transition(
            "tenant-a",
            act.id,
            status,
            actor_id=actor_id,
        )

    service._transition_internal(
        "tenant-a",
        act.id,
        ServiceActStatus.COMPLETED,
    )

    with pytest.raises(
        ValueError,
        match="invalid service act transition",
    ):
        service._transition_internal(
            "tenant-a",
            act.id,
            ServiceActStatus.CANCELLED,
            cancellation_reason="Too late",
        )


def test_cancellation_requires_reason(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    with pytest.raises(
        ValueError,
        match="cancellation reason is required",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.CANCELLED,
            actor_id=provider,
        )


def test_cancellation_records_reason_and_timestamp(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    act = service.transition(
        "tenant-a",
        act.id,
        ServiceActStatus.CANCELLED,
        cancellation_reason="Recipient cancelled the request.",
        actor_id=recipient,
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
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    tenant_b_actor = _create_user(
        connection,
        "tenant-b",
        "Tenant B Actor",
        with_permission=True,
    )

    service = _service(connection, repository)

    with pytest.raises(ValueError, match="service act not found"):
        service.transition(
            "tenant-b",
            act.id,
            ServiceActStatus.ACCEPTED,
            actor_id=tenant_b_actor,
        )


def test_service_act_cannot_be_completed_directly(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    with pytest.raises(
        PermissionError,
        match="service act actor is not authorized",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.COMPLETED,
            actor_id=provider,
        )


def test_service_act_requires_actor(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    with pytest.raises(
        PermissionError,
        match="service act actor is required",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.ACCEPTED,
        )


def test_service_act_requires_write_permission(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    unauthorized = _create_user(
        connection,
        "tenant-a",
        "Unauthorized",
        with_permission=False,
    )

    service = _service(connection, repository)

    with pytest.raises(
        PermissionError,
        match="service act permission denied",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.ACCEPTED,
            actor_id=unauthorized,
        )


@pytest.mark.parametrize(
    "target_status",
    [
        ServiceActStatus.ACCEPTED,
        ServiceActStatus.IN_PROGRESS,
        ServiceActStatus.SUBMITTED,
    ],
)
def test_service_act_actor_must_match_transition_role(
    tmp_path,
    monkeypatch,
    target_status,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    service = _service(connection, repository)

    actor_id = (
        provider
        if target_status == ServiceActStatus.ACCEPTED
        else recipient
    )

    with pytest.raises(
        PermissionError,
        match="service act actor is not authorized",
    ):
        service.transition(
            "tenant-a",
            act.id,
            target_status,
            actor_id=actor_id,
        )


def test_unrelated_same_tenant_actor_cannot_transition(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    unrelated = _create_user(
        connection,
        "tenant-a",
        "Unrelated",
        with_permission=True,
    )

    service = _service(connection, repository)

    with pytest.raises(
        PermissionError,
        match="service act actor is not authorized",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.ACCEPTED,
            actor_id=unrelated,
        )


def test_cross_tenant_actor_is_denied(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    repository, act, provider, recipient = _create_act(connection)

    other_tenant_actor = _create_user(
        connection,
        "tenant-b",
        "Other Tenant Actor",
        with_permission=True,
    )

    service = _service(connection, repository)

    with pytest.raises(
        PermissionError,
        match="service act permission denied",
    ):
        service.transition(
            "tenant-a",
            act.id,
            ServiceActStatus.ACCEPTED,
            actor_id=other_tenant_actor,
        )
