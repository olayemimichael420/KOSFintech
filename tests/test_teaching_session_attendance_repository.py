import sqlite3

import database
from models.teaching_session_attendance import TeachingSessionAttendance
from repositories.teaching_session_attendance_repository import (
    TeachingSessionAttendanceRepository,
)


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "cmos_attendance_repository.db"
    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed_relationship(connection, tenant_id="tenant-a", person_name="Member"):
    connection.execute(
        "INSERT INTO tenants (tenant_id) VALUES (?)",
        (tenant_id,),
    )

    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (person_name,),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        (person_name,),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO church_anchors (
            tenant_id,
            name,
            provenance_reference
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, f"Church {tenant_id}", "test-provenance"),
    )
    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO memberships (
            tenant_id,
            person_id,
            church_anchor_id,
            provenance_reference
        )
        VALUES (?, ?, ?, ?)
        """,
        (tenant_id, person_id, church_anchor_id, "test-provenance"),
    )
    membership_id = connection.execute(
        """
        SELECT id
        FROM memberships
        WHERE tenant_id = ?
          AND person_id = ?
        """,
        (tenant_id, person_id),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            tenant_id,
            f"Session {tenant_id}",
            "2026-01-01",
            "2026-03-31",
        ),
    )
    session_id = connection.execute(
        """
        SELECT id
        FROM teaching_sessions
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_session_members (
            tenant_id,
            teaching_session_id,
            membership_id
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, session_id, membership_id),
    )

    connection.commit()
    return session_id, membership_id


def _attendance(session_id, membership_id, date, status="present", remark=None):
    return TeachingSessionAttendance(
        id=None,
        tenant_id="tenant-a",
        teaching_session_id=session_id,
        membership_id=membership_id,
        attendance_date=date,
        status=status,
        remark=remark,
    )


def test_create_and_get(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_id, membership_id = _seed_relationship(connection)
    repository = TeachingSessionAttendanceRepository(connection)

    created = repository.create(
        _attendance(
            session_id,
            membership_id,
            "2026-01-15",
            status="late",
            remark="Arrived after commencement",
        )
    )

    assert created.id is not None
    assert created.status == "late"

    fetched = repository.get("tenant-a", created.id)

    assert fetched == created


def test_list_by_tenant_is_tenant_scoped(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_a, member_a = _seed_relationship(connection)
    session_b, member_b = _seed_relationship(
        connection,
        tenant_id="tenant-b",
        person_name="Member B",
    )
    repository = TeachingSessionAttendanceRepository(connection)

    repository.create(_attendance(session_a, member_a, "2026-01-15"))

    repository.create(
        TeachingSessionAttendance(
            id=None,
            tenant_id="tenant-b",
            teaching_session_id=session_b,
            membership_id=member_b,
            attendance_date="2026-01-15",
        )
    )

    results = repository.list_by_tenant("tenant-a")

    assert len(results) == 1
    assert results[0].tenant_id == "tenant-a"


def test_list_by_session(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_id, membership_id = _seed_relationship(connection)
    repository = TeachingSessionAttendanceRepository(connection)

    repository.create(_attendance(session_id, membership_id, "2026-01-15"))
    repository.create(_attendance(session_id, membership_id, "2026-01-22"))

    results = repository.list_by_session("tenant-a", session_id)

    assert [item.attendance_date for item in results] == [
        "2026-01-15",
        "2026-01-22",
    ]


def test_list_by_member(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_id, membership_id = _seed_relationship(connection)
    repository = TeachingSessionAttendanceRepository(connection)

    repository.create(_attendance(session_id, membership_id, "2026-01-15"))
    repository.create(_attendance(session_id, membership_id, "2026-01-22"))

    results = repository.list_by_member("tenant-a", membership_id)

    assert len(results) == 2
    assert all(item.membership_id == membership_id for item in results)


def test_list_by_date(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_id, membership_id = _seed_relationship(connection)
    repository = TeachingSessionAttendanceRepository(connection)

    repository.create(_attendance(session_id, membership_id, "2026-01-15"))

    results = repository.list_by_date("tenant-a", "2026-01-15")

    assert len(results) == 1
    assert results[0].attendance_date == "2026-01-15"


def test_get_unknown_returns_none(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    repository = TeachingSessionAttendanceRepository(connection)

    assert repository.get("tenant-a", 999999) is None


def test_create_preserves_frozen_model_input(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    session_id, membership_id = _seed_relationship(connection)
    repository = TeachingSessionAttendanceRepository(connection)

    attendance = _attendance(
        session_id,
        membership_id,
        "2026-01-15",
    )

    created = repository.create(attendance)

    assert attendance.id is None
    assert created.id is not None
    assert created != attendance
