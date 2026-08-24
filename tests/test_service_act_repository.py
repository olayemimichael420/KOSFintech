import database

from models.service_act import ServiceAct, ServiceActStatus
from repositories.service_act_repository import ServiceActRepository


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_repository.db"
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


def _make_act(tenant_id, provider_id, recipient_id, title="Tutoring"):
    return ServiceAct(
        id=None,
        tenant_id=tenant_id,
        provider_user_id=provider_id,
        recipient_user_id=recipient_id,
        title=title,
        description="Provide mathematics tutoring.",
    )


def test_create_and_get_service_act(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(connection, "tenant-a", "Provider")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceActRepository(connection)
        act = repository.create(
            _make_act("tenant-a", provider, recipient)
        )

        assert act.id is not None
        assert act.status == ServiceActStatus.CREATED

        loaded = repository.get("tenant-a", act.id)

        assert loaded is not None
        assert loaded.id == act.id
        assert loaded.tenant_id == "tenant-a"
        assert loaded.provider_user_id == provider
        assert loaded.recipient_user_id == recipient
        assert loaded.title == "Tutoring"
    finally:
        connection.close()


def test_get_is_tenant_scoped(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(connection, "tenant-a", "Provider")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        repository = ServiceActRepository(connection)
        act = repository.create(
            _make_act("tenant-a", provider, recipient)
        )

        assert repository.get("tenant-a", act.id) is not None
        assert repository.get("tenant-b", act.id) is None
    finally:
        connection.close()


def test_list_by_tenant(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider_a = _create_user(connection, "tenant-a", "Provider A")
        recipient_a = _create_user(connection, "tenant-a", "Recipient A")
        provider_b = _create_user(connection, "tenant-b", "Provider B")
        recipient_b = _create_user(connection, "tenant-b", "Recipient B")

        repository = ServiceActRepository(connection)

        repository.create(
            _make_act("tenant-a", provider_a, recipient_a, "Act A")
        )
        repository.create(
            _make_act("tenant-b", provider_b, recipient_b, "Act B")
        )

        acts = repository.list_by_tenant("tenant-a")

        assert len(acts) == 1
        assert acts[0].title == "Act A"
    finally:
        connection.close()


def test_list_by_provider_and_recipient(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(connection, "tenant-a", "Provider")
        recipient = _create_user(connection, "tenant-a", "Recipient")
        other = _create_user(connection, "tenant-a", "Other")

        repository = ServiceActRepository(connection)

        repository.create(
            _make_act("tenant-a", provider, recipient, "Act 1")
        )
        repository.create(
            _make_act("tenant-a", provider, other, "Act 2")
        )
        repository.create(
            _make_act("tenant-a", other, recipient, "Act 3")
        )

        provider_acts = repository.list_by_provider(
            "tenant-a",
            provider,
        )
        recipient_acts = repository.list_by_recipient(
            "tenant-a",
            recipient,
        )

        assert [act.title for act in provider_acts] == [
            "Act 1",
            "Act 2",
        ]

        assert [act.title for act in recipient_acts] == [
            "Act 1",
            "Act 3",
        ]
    finally:
        connection.close()
