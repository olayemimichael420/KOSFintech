import sqlite3

import pytest
import database
from models.church_activity import ChurchActivity, ChurchActivityDeliveryMode, ChurchActivityStatus
from repositories.church_activity_repository import ChurchActivityRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "church_activity_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')", ("tenant-a",))
    connection.execute("INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')", ("tenant-b",))
    connection.commit()
    return connection


def test_create_and_get(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)
    created = repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Sunday Worship", activity_type="worship", purpose="Congregational worship"))
    assert created.id is not None
    assert created.tenant_id == "tenant-a"
    assert created.name == "Sunday Worship"
    loaded = repository.get("tenant-a", created.id)
    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.tenant_id == "tenant-a"
    assert loaded.name == "Sunday Worship"
    assert loaded.activity_type == "worship"
    assert loaded.status == ChurchActivityStatus.DRAFT
    assert loaded.delivery_mode == ChurchActivityDeliveryMode.PHYSICAL
    assert loaded.created_at is not None
    connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)
    created = repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Bible Study", activity_type="teaching"))
    assert repository.get("tenant-a", created.id) is not None
    assert repository.get("tenant-b", created.id) is None
    connection.close()


def test_list_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)
    repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Activity A", activity_type="worship"))
    repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Activity B", activity_type="fellowship"))
    repository.create(ChurchActivity(id=None, tenant_id="tenant-b", name="Other Activity", activity_type="outreach"))
    activities = repository.list("tenant-a")
    assert [activity.name for activity in activities] == ["Activity A", "Activity B"]
    assert all(activity.tenant_id == "tenant-a" for activity in activities)
    connection.close()


def test_missing_activity_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)
    assert repository.get("tenant-a", 999999) is None
    connection.close()


def test_activity_can_exist_without_program(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)
    created = repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Open Prayer", activity_type="prayer"))
    loaded = repository.get("tenant-a", created.id)
    assert loaded is not None
    assert loaded.program_id is None
    connection.close()


def test_activity_can_reference_same_tenant_program(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    connection.execute("INSERT INTO church_programs (tenant_id, name) VALUES (?, ?)", ("tenant-a", "Discipleship"))
    program_id = connection.execute("SELECT id FROM church_programs WHERE tenant_id = ? AND name = ?", ("tenant-a", "Discipleship")).fetchone()[0]
    connection.commit()
    repository = ChurchActivityRepository(connection)
    created = repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Discipleship Session", activity_type="teaching", program_id=program_id))
    loaded = repository.get("tenant-a", created.id)
    assert loaded is not None
    assert loaded.program_id == program_id
    connection.close()


def test_activity_rejects_cross_tenant_program(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    connection.execute("INSERT INTO church_programs (tenant_id, name) VALUES (?, ?)", ("tenant-b", "Restricted Program"))
    program_id = connection.execute("SELECT id FROM church_programs WHERE tenant_id = ? AND name = ?", ("tenant-b", "Restricted Program")).fetchone()[0]
    connection.commit()
    repository = ChurchActivityRepository(connection)
    with pytest.raises(sqlite3.IntegrityError):
        repository.create(ChurchActivity(id=None, tenant_id="tenant-a", name="Invalid Cross Tenant Activity", activity_type="teaching", program_id=program_id))
    connection.close()


def test_all_delivery_modes_round_trip_with_stable_persisted_values(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchActivityRepository(connection)

    expected_modes = [
        ChurchActivityDeliveryMode.PHYSICAL,
        ChurchActivityDeliveryMode.ONLINE,
        ChurchActivityDeliveryMode.LIVE_STREAM,
        ChurchActivityDeliveryMode.HYBRID,
        ChurchActivityDeliveryMode.RECORDED,
        ChurchActivityDeliveryMode.ON_DEMAND,
    ]

    created_ids = []

    for mode in expected_modes:
        created = repository.create(
            ChurchActivity(
                id=None,
                tenant_id="tenant-a",
                name=f"Activity {mode.value}",
                activity_type="teaching",
                delivery_mode=mode,
            )
        )
        created_ids.append(created.id)

    persisted = connection.execute(
        """
        SELECT delivery_mode
        FROM church_activities
        WHERE tenant_id = ?
        ORDER BY id
        """,
        ("tenant-a",),
    ).fetchall()

    assert [row["delivery_mode"] for row in persisted] == [
        mode.value for mode in expected_modes
    ]

    loaded = [
        repository.get("tenant-a", activity_id)
        for activity_id in created_ids
    ]

    assert [activity.delivery_mode for activity in loaded] == expected_modes

    connection.close()
