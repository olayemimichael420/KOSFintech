import sqlite3

import pytest

import database


def test_teacher_students_reject_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "teacher_student_cross_tenant.db"

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
                "school-A",
                None,
                "Teacher A",
                "Mathematics",
                "B.Ed",
                "active",
            ),
        )

        teacher_id = connection.execute(
            """
            SELECT id
            FROM teachers
            WHERE name = ?
            """,
            ("Teacher A",),
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
                "school-B",
                None,
                "Student B",
                "JSS 1",
                12,
                None,
                None,
                "active",
            ),
        )

        student_id = connection.execute(
            """
            SELECT id
            FROM students
            WHERE name = ?
            """,
            ("Student B",),
        ).fetchone()["id"]

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teacher_students (
                    tenant_id,
                    teacher_id,
                    student_id
                )
                VALUES (?, ?, ?)
                """,
                (
                    "school-A",
                    teacher_id,
                    student_id,
                ),
            )

    finally:
        connection.close()
