import sqlite3

import pytest
import database


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "grade_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_grades_schema_columns(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    rows = connection.execute(
        "PRAGMA table_info(grades)"
    ).fetchall()

    columns = {
        row["name"]: row["type"]
        for row in rows
    }

    assert columns == {
        "id": "INTEGER",
        "tenant_id": "TEXT",
        "name": "TEXT",
        "description": "TEXT",
        "minimum_score": "INTEGER",
        "maximum_score": "INTEGER",
        "status": "TEXT",
    }


def test_grades_tenant_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(grades)"
    ).fetchall()

    assert any(
        row["table"] == "tenants"
        and row["from"] == "tenant_id"
        and row["to"] == "tenant_id"
        for row in foreign_keys
    )


def test_grades_identity_index(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    indexes = connection.execute(
        "PRAGMA index_list(grades)"
    ).fetchall()

    index_names = {row["name"] for row in indexes}

    assert "ux_grades_id_tenant" in index_names


def test_grades_name_unique_per_tenant(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-a",),
    )

    connection.execute(
        """
        INSERT INTO grades (
            tenant_id,
            name,
            minimum_score,
            maximum_score
        )
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-a", "A", 80, 100),
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO grades (
                tenant_id,
                name,
                minimum_score,
                maximum_score
            )
            VALUES (?, ?, ?, ?)
            """,
            ("tenant-a", "A", 80, 100),
        )
