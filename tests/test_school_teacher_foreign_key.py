import sqlite3

import pytest

import database


def test_school_teachers_enforce_teacher_foreign_key(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "school_teacher_fk.db"

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
                "school-001",
                None,
                "Test Teacher",
                "Mathematics",
                "B.Ed",
                "active",
            ),
        )

        teacher_id = connection.execute(
            "SELECT id FROM teachers WHERE name = ?",
            ("Test Teacher",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO school_teachers (
                tenant_id,
                teacher_id
            )
            VALUES (?, ?)
            """,
            ("school-001", teacher_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, teacher_id
            FROM school_teachers
            WHERE teacher_id = ?
            """,
            (teacher_id,),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_teachers (
                    tenant_id,
                    teacher_id
                )
                VALUES (?, ?)
                """,
                ("school-001", 999999),
            )

    finally:
        connection.close()
