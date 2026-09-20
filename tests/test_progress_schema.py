import sqlite3

import pytest
import database


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "progress_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_progresses_schema_columns(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    rows = connection.execute(
        "PRAGMA table_info(progresses)"
    ).fetchall()

    columns = {
        row["name"]: row["type"]
        for row in rows
    }

    assert columns == {
        "id": "INTEGER",
        "tenant_id": "TEXT",
        "membership_id": "INTEGER",
        "teaching_content_id": "INTEGER",
        "progress_date": "DATE",
        "description": "TEXT",
        "remark": "TEXT",
        "status": "TEXT",
    }


def test_progresses_membership_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(progresses)"
    ).fetchall()

    assert any(
        row["table"] == "memberships"
        and row["from"] == "membership_id"
        and row["to"] == "id"
        for row in foreign_keys
    )


def test_progresses_teaching_content_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(progresses)"
    ).fetchall()

    assert any(
        row["table"] == "teaching_contents"
        and row["from"] == "teaching_content_id"
        and row["to"] == "id"
        for row in foreign_keys
    )


def test_progresses_identity_index(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    indexes = connection.execute(
        "PRAGMA index_list(progresses)"
    ).fetchall()

    index_names = {row["name"] for row in indexes}

    assert "ux_progresses_id_tenant" in index_names


def test_progresses_status_constraint(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO progresses (
                tenant_id,
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-cmos",
                999999,
                999999,
                "2026-09-19",
                "Invalid status test",
                "invalid",
            ),
        )
