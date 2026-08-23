import sqlite3

import pytest

import database


def test_school_teachers_reject_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "school_teacher_cross_tenant.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()
    connection = database.get_connection()

    try:
        connection.execute(
            """
            INSERT INTO teachers (
                tenant_id,
                user_id,
                name,
                subject,
                qualification,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "school-B",
                None,
                "Teacher B",
                "Mathematics",
                "B.Ed",
                "active",
            ),
        )

        teacher_id = connection.execute(
            "SELECT id FROM teachers WHERE name = ?",
            ("Teacher B",),
        ).fetchone()["id"]

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_teachers (
                    tenant_id,
                    teacher_id
                )
                VALUES (?, ?)
                """,
                ("school-A", teacher_id),
            )

    finally:
        connection.close()
