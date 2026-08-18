import sqlite3

import pytest

import database


def test_teacher_students_enforce_student_foreign_key(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "teacher_student_student_fk.db"

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
            INSERT INTO teacher_students (
                teacher_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (teacher_id, student_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT teacher_id, student_id
            FROM teacher_students
            WHERE teacher_id = ?
              AND student_id = ?
            """,
            (teacher_id, student_id),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teacher_students (
                    teacher_id,
                    student_id
                )
                VALUES (?, ?)
                """,
                (teacher_id, 999999),
            )

    finally:
        connection.close()
