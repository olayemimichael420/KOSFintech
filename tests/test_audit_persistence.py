import json

import database
from audit import audit_event


def test_audit_event_is_persisted(tmp_path, monkeypatch):
    db_path = tmp_path / "audit_persistence.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()

    audit_event(
        event_type="audit_persistence_test",
        actor_id=9001,
        tenant_id="audit-test",
        action="verify_persistence",
        metadata={
            "source": "automated_test",
            "value": 123,
        },
    )

    connection = database.get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            timestamp,
            event_type,
            actor_id,
            tenant_id,
            action,
            metadata
        FROM audit_events
        WHERE event_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        ("audit_persistence_test",),
    ).fetchone()

    connection.close()

    assert row is not None
    assert row["id"] is not None
    assert row["timestamp"]
    assert row["event_type"] == "audit_persistence_test"
    assert row["actor_id"] == 9001
    assert row["tenant_id"] == "audit-test"
    assert row["action"] == "verify_persistence"

    metadata = json.loads(row["metadata"])

    assert metadata["source"] == "automated_test"
    assert metadata["value"] == 123
