from datetime import datetime, timezone

import database
from models.audit_event import AuditEvent
from repositories.audit_event_repository import AuditEventRepository


def test_audit_event_repository_create_get_and_list(tmp_path, monkeypatch):
    db_path = tmp_path / "audit_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    repository = AuditEventRepository(connection)

    event = AuditEvent(
        id=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="repository_test",
        actor_id=7001,
        tenant_id="tenant-a",
        action="repository_create",
        metadata={
            "test": True,
            "value": 42,
        },
    )

    created = repository.create(event)

    assert created.id is not None
    assert created.event_type == "repository_test"
    assert created.actor_id == 7001
    assert created.tenant_id == "tenant-a"
    assert created.action == "repository_create"
    assert created.metadata["test"] is True
    assert created.metadata["value"] == 42

    fetched = repository.get(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.tenant_id == "tenant-a"
    assert fetched.metadata["value"] == 42

    events = repository.list_by_tenant("tenant-a")

    assert len(events) == 1
    assert events[0].id == created.id

    connection.close()


def test_audit_event_repository_is_tenant_scoped(tmp_path, monkeypatch):
    db_path = tmp_path / "audit_tenant_scope.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    repository = AuditEventRepository(connection)

    repository.create(
        AuditEvent(
            id=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="tenant_a_event",
            actor_id=1,
            tenant_id="tenant-a",
            action="test",
            metadata={},
        )
    )

    repository.create(
        AuditEvent(
            id=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="tenant_b_event",
            actor_id=2,
            tenant_id="tenant-b",
            action="test",
            metadata={},
        )
    )

    tenant_a_events = repository.list_by_tenant("tenant-a")
    tenant_b_events = repository.list_by_tenant("tenant-b")

    assert len(tenant_a_events) == 1
    assert tenant_a_events[0].tenant_id == "tenant-a"

    assert len(tenant_b_events) == 1
    assert tenant_b_events[0].tenant_id == "tenant-b"

    connection.close()
