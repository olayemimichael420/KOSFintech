import database

from models.service_request import ServiceRequest, ServiceRequestStatus
from repositories.service_request_repository import ServiceRequestRepository


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_request_repository.db"
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


def _make_request(
    tenant_id,
    requester_id,
    recipient_id,
    title="Mathematics Support",
):
    return ServiceRequest(
        id=None,
        tenant_id=tenant_id,
        requester_user_id=requester_id,
        recipient_user_id=recipient_id,
        title=title,
        description="Request mathematics support.",
    )


def test_create_and_get_service_request(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        request = repository.create(
            _make_request("tenant-a", requester, recipient)
        )

        assert request.id is not None
        assert request.status == ServiceRequestStatus.REQUESTED

        loaded = repository.get("tenant-a", request.id)

        assert loaded is not None
        assert loaded.id == request.id
        assert loaded.tenant_id == "tenant-a"
        assert loaded.requester_user_id == requester
        assert loaded.recipient_user_id == recipient
        assert loaded.title == "Mathematics Support"
        assert loaded.description == "Request mathematics support."
    finally:
        connection.close()


def test_get_is_tenant_scoped(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceRequestRepository(connection)
        request = repository.create(
            _make_request("tenant-a", requester, recipient)
        )

        assert repository.get("tenant-a", request.id) is not None
        assert repository.get("tenant-b", request.id) is None
    finally:
        connection.close()


def test_list_by_tenant(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester_a = _create_user(connection, "tenant-a", "Requester A")
        recipient_a = _create_user(connection, "tenant-a", "Recipient A")
        requester_b = _create_user(connection, "tenant-b", "Requester B")
        recipient_b = _create_user(connection, "tenant-b", "Recipient B")

        repository = ServiceRequestRepository(connection)

        repository.create(
            _make_request(
                "tenant-a",
                requester_a,
                recipient_a,
                "Request A",
            )
        )
        repository.create(
            _make_request(
                "tenant-b",
                requester_b,
                recipient_b,
                "Request B",
            )
        )

        requests = repository.list_by_tenant("tenant-a")

        assert len(requests) == 1
        assert requests[0].title == "Request A"
    finally:
        connection.close()


def test_list_by_requester_and_recipient(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        requester = _create_user(connection, "tenant-a", "Requester")
        recipient = _create_user(connection, "tenant-a", "Recipient")
        other = _create_user(connection, "tenant-a", "Other")

        repository = ServiceRequestRepository(connection)

        repository.create(
            _make_request(
                "tenant-a",
                requester,
                recipient,
                "Request 1",
            )
        )
        repository.create(
            _make_request(
                "tenant-a",
                requester,
                other,
                "Request 2",
            )
        )
        repository.create(
            _make_request(
                "tenant-a",
                other,
                recipient,
                "Request 3",
            )
        )

        requester_requests = repository.list_by_requester(
            "tenant-a",
            requester,
        )
        recipient_requests = repository.list_by_recipient(
            "tenant-a",
            recipient,
        )

        assert [request.title for request in requester_requests] == [
            "Request 1",
            "Request 2",
        ]
        assert [request.title for request in recipient_requests] == [
            "Request 1",
            "Request 3",
        ]
    finally:
        connection.close()
