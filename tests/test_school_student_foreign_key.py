import sqlite3

import pytest

import database


def test_school_students_enforce_student_foreign_key(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "school_student_fk.db"

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
            INSERT INTO students (
                tenant_id,
                user_id,
                name,
                class_name,
                age,
                guardian_id,
                enrollment_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "school-001",
                None,
                "Test Student",
                "Primary 1",
                7,
                None,
                None,
                "active",
            ),
        )

        student_id = connection.execute(
            "SELECT id FROM students WHERE name = ?",
            ("Test Student",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO school_students (
                tenant_id,
                student_id
            )
            VALUES (?, ?)
            """,
            ("school-001", student_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, student_id
            FROM school_students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_students (
                    tenant_id,
                    student_id
                )
                VALUES (?, ?)
                """,
                ("school-001", 999999),
            )

    finally:
        connection.close()
