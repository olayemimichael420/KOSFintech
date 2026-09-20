import pytest
import sqlite3

import database


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "cmos_attendance_schema.db"
    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed_valid_relationship(connection):
    connection.execute(
        """
        INSERT INTO tenants (tenant_id)
        VALUES ('tenant-a')
        """
    )
    connection.execute(
        """
        INSERT INTO persons (name)
        VALUES ('Member One')
        """
    )
    connection.execute(
        """
        INSERT INTO church_anchors (
            tenant_id,
            name,
            provenance_reference
        )
        VALUES ('tenant-a', 'Church A', 'test-provenance')
        """
    )
    church_anchor_id = connection.execute(
        "SELECT id FROM church_anchors WHERE tenant_id = 'tenant-a'"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO memberships (
            tenant_id,
            person_id,
            church_anchor_id,
            provenance_reference
        )
        VALUES ('tenant-a', 1, ?, 'test-provenance')
        """,
        (church_anchor_id,),
    )
    membership_id = connection.execute(
        "SELECT id FROM memberships WHERE tenant_id = 'tenant-a'"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id,
            name,
            start_date,
            end_date
        )
        VALUES ('tenant-a', 'Session A', '2026-01-01', '2026-03-31')
        """
    )
    teaching_session_id = connection.execute(
        "SELECT id FROM teaching_sessions WHERE tenant_id = 'tenant-a'"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_session_members (
            tenant_id,
            teaching_session_id,
            membership_id
        )
        VALUES ('tenant-a', ?, ?)
        """,
        (teaching_session_id, membership_id),
    )

    connection.commit()
    return teaching_session_id, membership_id


def test_teaching_session_attendance_accepts_valid_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)
    teaching_session_id, membership_id = _seed_valid_relationship(connection)

    connection.execute(
        """
        INSERT INTO teaching_session_attendance (
            tenant_id,
            teaching_session_id,
            membership_id,
            attendance_date
        )
        VALUES ('tenant-a', ?, ?, '2026-01-15')
        """,
        (teaching_session_id, membership_id),
    )

    connection.commit()

    row = connection.execute(
        """
        SELECT
            tenant_id,
            teaching_session_id,
            membership_id,
            attendance_date,
            status,
            remark
        FROM teaching_session_attendance
        """
    ).fetchone()

    assert tuple(row) == (
        "tenant-a",
        teaching_session_id,
        membership_id,
        "2026-01-15",
        "present",
        None,
    )


def test_teaching_session_attendance_rejects_missing_session_member(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)
    _seed_valid_relationship(connection)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO teaching_session_attendance (
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date
            )
            VALUES ('tenant-a', 999999, 1, '2026-01-15')
            """
        )


def test_teaching_session_attendance_rejects_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)
    teaching_session_id, membership_id = _seed_valid_relationship(connection)

    connection.execute(
        """
        INSERT INTO tenants (tenant_id)
        VALUES ('tenant-b')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO teaching_session_attendance (
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date
            )
            VALUES ('tenant-b', ?, ?, '2026-01-15')
            """,
            (teaching_session_id, membership_id),
        )


def test_teaching_session_attendance_rejects_duplicate_same_date(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)
    teaching_session_id, membership_id = _seed_valid_relationship(connection)

    values = (
        "tenant-a",
        teaching_session_id,
        membership_id,
        "2026-01-15",
    )

    connection.execute(
        """
        INSERT INTO teaching_session_attendance (
            tenant_id,
            teaching_session_id,
            membership_id,
            attendance_date
        )
        VALUES (?, ?, ?, ?)
        """,
        values,
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO teaching_session_attendance (
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date
            )
            VALUES (?, ?, ?, ?)
            """,
            values,
        )


def test_teaching_session_attendance_allows_different_dates(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)
    teaching_session_id, membership_id = _seed_valid_relationship(connection)

    for attendance_date in ("2026-01-15", "2026-01-22"):
        connection.execute(
            """
            INSERT INTO teaching_session_attendance (
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "tenant-a",
                teaching_session_id,
                membership_id,
                attendance_date,
            ),
        )

    connection.commit()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM teaching_session_attendance
        """
    ).fetchone()[0]

    assert count == 2
