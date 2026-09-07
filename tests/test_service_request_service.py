import database
import pytest

from models.service_request import ServiceRequest, ServiceRequestStatus
from repositories.service_request_repository import ServiceRequestRepository
from services.permission_resolution_service import PermissionResolutionService
from services.service_request_service import ServiceRequestService


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_request_service.db"
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
        role_name = f"service-request-{user_id}"

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
            VALUES (?, 'service_request.write', 'active')
            """,
            (tenant_id,),
        )

        permission_id = connection.execute(
            """
            SELECT id
            FROM permissions
            WHERE tenant_id = ?
              AND name = 'service_request.write'
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


def _make_request(tenant_id, requester_id, recipient_id):
    return ServiceRequest(
        id=None,
        tenant_id=tenant_id,
        requester_user_id=requester_id,
        recipient_user_id=recipient_id,
        title="Mathematics Support",
        description="Request mathematics support.",
    )


def _service(connection, repository):
    permission_service = PermissionResolutionService(connection)
    return ServiceRequestService(
        repository,
        permission_service,
    )


def test_create_requires_requester_as_actor(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        with pytest.raises(
            PermissionError,
            match="service request actor is not the requester",
        ):
            service.create(
                _make_request("tenant-a", requester, recipient),
                actor_id=recipient,
            )
    finally:
        connection.close()


def test_create_requires_write_permission(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(
            connection,
            "tenant-a",
            "Requester",
            with_permission=False,
        )
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        with pytest.raises(
            PermissionError,
            match="service request permission denied",
        ):
            service.create(
                _make_request("tenant-a", requester, recipient),
                actor_id=requester,
            )
    finally:
        connection.close()


def test_create_rejects_requester_equal_to_recipient(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        with pytest.raises(
            ValueError,
            match="requester and recipient must differ",
        ):
            service.create(
                _make_request("tenant-a", requester, requester),
                actor_id=requester,
            )
    finally:
        connection.close()


def test_create_service_request(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        assert request.id is not None
        assert request.status == ServiceRequestStatus.REQUESTED
        assert request.requester_user_id == requester
        assert request.recipient_user_id == recipient
    finally:
        connection.close()


def test_only_requester_can_authorize(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        with pytest.raises(
            PermissionError,
            match="service request actor is not authorized",
        ):
            service.transition(
                "tenant-a",
                request.id,
                ServiceRequestStatus.AUTHORIZED,
                actor_id=recipient,
            )

        authorized = service.transition(
            "tenant-a",
            request.id,
            ServiceRequestStatus.AUTHORIZED,
            actor_id=requester,
        )

        assert authorized.status == ServiceRequestStatus.AUTHORIZED
        assert authorized.authorized_at is not None
    finally:
        connection.close()


def test_cancellation_requires_reason(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        with pytest.raises(
            ValueError,
            match="cancellation reason is required",
        ):
            service.transition(
                "tenant-a",
                request.id,
                ServiceRequestStatus.CANCELLED,
                actor_id=requester,
            )
    finally:
        connection.close()


def test_cancellation_records_reason_and_timestamp(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        cancelled = service.transition(
            "tenant-a",
            request.id,
            ServiceRequestStatus.CANCELLED,
            cancellation_reason="Request withdrawn.",
            actor_id=requester,
        )

        assert cancelled.status == ServiceRequestStatus.CANCELLED
        assert cancelled.cancelled_at is not None
        assert cancelled.cancellation_reason == "Request withdrawn."
    finally:
        connection.close()


def test_service_request_transition_is_tenant_scoped(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")
        tenant_b_actor = _create_user(
            connection,
            "tenant-b",
            "Tenant B Actor",
        )

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        with pytest.raises(
            ValueError,
            match="service request not found",
        ):
            service.transition(
                "tenant-b",
                request.id,
                ServiceRequestStatus.AUTHORIZED,
                actor_id=tenant_b_actor,
            )
    finally:
        connection.close()

def test_create_service_request_records_audit_event(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        event = connection.execute(
            """
            SELECT event_type, actor_id, tenant_id, action, metadata
            FROM audit_events
            WHERE event_type = 'service_request_created'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        assert event is not None
        assert event["actor_id"] == requester
        assert event["tenant_id"] == "tenant-a"
        assert event["action"] == "create_service_request"
        assert str(request.id) in event["metadata"]
    finally:
        connection.close()

def test_authorize_service_request_records_audit_event(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        service.transition(
            tenant_id="tenant-a",
            request_id=request.id,
            target_status=ServiceRequestStatus.AUTHORIZED,
            actor_id=requester,
        )

        event = connection.execute(
            """
            SELECT event_type, actor_id, tenant_id, action, metadata
            FROM audit_events
            WHERE event_type = 'service_request_authorized'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        assert event is not None
        assert event["actor_id"] == requester
        assert event["tenant_id"] == "tenant-a"
        assert event["action"] == "authorize_service_request"
        assert str(request.id) in event["metadata"]
    finally:
        connection.close()

def test_cancel_service_request_records_audit_event(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        reason = "Requester no longer needs support."

        service.transition(
            tenant_id="tenant-a",
            request_id=request.id,
            target_status=ServiceRequestStatus.CANCELLED,
            cancellation_reason=reason,
            actor_id=requester,
        )

        event = connection.execute(
            """
            SELECT event_type, actor_id, tenant_id, action, metadata
            FROM audit_events
            WHERE event_type = 'service_request_cancelled'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        assert event is not None
        assert event["actor_id"] == requester
        assert event["tenant_id"] == "tenant-a"
        assert event["action"] == "cancel_service_request"
        assert str(request.id) in event["metadata"]
        assert reason in event["metadata"]
    finally:
        connection.close()

def test_create_service_request_rolls_back_when_audit_fails(
    tmp_path, monkeypatch
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        def fail_audit(*args, **kwargs):
            raise RuntimeError("audit failure")

        monkeypatch.setattr(
            "services.service_request_service.audit_event",
            fail_audit,
        )

        with pytest.raises(RuntimeError, match="audit failure"):
            service.create(
                _make_request("tenant-a", requester, recipient),
                actor_id=requester,
            )

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM service_requests
            WHERE tenant_id = 'tenant-a'
            """
        ).fetchone()[0]

        assert count == 0
    finally:
        connection.close()

def test_authorize_service_request_rolls_back_when_audit_fails(
    tmp_path, monkeypatch
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        def fail_audit(*args, **kwargs):
            raise RuntimeError("audit failure")

        monkeypatch.setattr(
            "services.service_request_service.audit_event",
            fail_audit,
        )

        with pytest.raises(RuntimeError, match="audit failure"):
            service.transition(
                tenant_id="tenant-a",
                request_id=request.id,
                target_status=ServiceRequestStatus.AUTHORIZED,
                actor_id=requester,
            )

        current = repository.get("tenant-a", request.id)

        assert current is not None
        assert current.status == ServiceRequestStatus.REQUESTED
        assert current.authorized_at is None
    finally:
        connection.close()

def test_cancel_service_request_rolls_back_when_audit_fails(
    tmp_path, monkeypatch
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        service = _service(connection, repository)

        request = service.create(
            _make_request("tenant-a", requester, recipient),
            actor_id=requester,
        )

        reason = "Requester no longer needs support."

        def fail_audit(*args, **kwargs):
            raise RuntimeError("audit failure")

        monkeypatch.setattr(
            "services.service_request_service.audit_event",
            fail_audit,
        )

        with pytest.raises(RuntimeError, match="audit failure"):
            service.transition(
                tenant_id="tenant-a",
                request_id=request.id,
                target_status=ServiceRequestStatus.CANCELLED,
                cancellation_reason=reason,
                actor_id=requester,
            )

        current = repository.get("tenant-a", request.id)

        assert current is not None
        assert current.status == ServiceRequestStatus.REQUESTED
        assert current.cancelled_at is None
        assert current.cancellation_reason is None
    finally:
        connection.close()
