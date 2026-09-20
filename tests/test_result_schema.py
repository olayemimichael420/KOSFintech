import sqlite3

import pytest
import database


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "result_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_results_schema_columns(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    rows = connection.execute(
        "PRAGMA table_info(results)"
    ).fetchall()

    columns = {
        row["name"]: row["type"]
        for row in rows
    }

    assert columns == {
        "id": "INTEGER",
        "tenant_id": "TEXT",
        "assessment_id": "INTEGER",
        "membership_id": "INTEGER",
        "grade_id": "INTEGER",
        "result": "TEXT",
        "result_date": "DATE",
        "remark": "TEXT",
        "status": "TEXT",
    }


def test_results_assessment_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(results)"
    ).fetchall()

    assert any(
        row["table"] == "assessments"
        and row["from"] == "assessment_id"
        and row["to"] == "id"
        for row in foreign_keys
    )


def test_results_membership_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(results)"
    ).fetchall()

    assert any(
        row["table"] == "memberships"
        and row["from"] == "membership_id"
        and row["to"] == "id"
        for row in foreign_keys
    )


def test_results_grade_foreign_key(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    foreign_keys = connection.execute(
        "PRAGMA foreign_key_list(results)"
    ).fetchall()

    assert any(
        row["table"] == "grades"
        and row["from"] == "grade_id"
        and row["to"] == "id"
        for row in foreign_keys
    )


def test_results_identity_index(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    indexes = connection.execute(
        "PRAGMA index_list(results)"
    ).fetchall()

    index_names = {row["name"] for row in indexes}

    assert "ux_results_id_tenant" in index_names


def test_results_unique_per_assessment_member(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)

    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-a",),
    )

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
        ("tenant-a", "Session A", "2026-09-19", "2026-09-19"),
    )

    session_id = connection.execute(
        "SELECT id FROM teaching_sessions WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_series (
            tenant_id,
            teaching_session_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("tenant-a", session_id, "Series A", "2026-09-19", "2026-09-19"),
    )

    series_id = connection.execute(
        "SELECT id FROM teaching_series WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_focuses (
            tenant_id,
            teaching_series_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("tenant-a", series_id, "Focus A", "2026-09-19", "2026-09-19"),
    )

    focus_id = connection.execute(
        "SELECT id FROM teaching_focuses WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_contents (
            tenant_id,
            teaching_focus_id,
            name
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-a", focus_id, "Content A"),
    )

    content_id = connection.execute(
        "SELECT id FROM teaching_contents WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO assessments (
            tenant_id,
            teaching_content_id,
            name,
            assessment_date
        )
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-a", content_id, "Assessment A", "2026-09-19"),
    )

    assessment_id = connection.execute(
        "SELECT id FROM assessments WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

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

    grade_id = connection.execute(
        "SELECT id FROM grades WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    person_id = connection.execute(
        """
        INSERT INTO persons (name)
        VALUES (?)
        RETURNING id
        """,
        ("Member A",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO church_anchors (
            tenant_id,
            name,
            provenance_reference
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-a", "Church A", "church-a-provenance"),
    )

    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = ?
        """,
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO memberships (
            tenant_id,
            person_id,
            church_anchor_id,
            membership_status,
            provenance_reference
        )
        VALUES (?, ?, ?, 'active', ?)
        """,
        (
            "tenant-a",
            person_id,
            church_anchor_id,
            "membership-test",
        ),
    )

    membership_id = connection.execute(
        """
        SELECT id
        FROM memberships
        WHERE tenant_id = ?
        """,
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO results (
            tenant_id,
            assessment_id,
            membership_id,
            grade_id,
            result,
            result_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            assessment_id,
            membership_id,
            grade_id,
            "Completed the assessment requirements",
            "2026-09-19",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO results (
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-a",
                assessment_id,
                membership_id,
                grade_id,
                "Duplicate result",
                "2026-09-19",
            ),
        )
