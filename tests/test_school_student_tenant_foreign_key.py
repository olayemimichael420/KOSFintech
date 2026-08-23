import sqlite3

import pytest

import database


def test_school_students_reject_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "school_student_cross_tenant.db"

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
            "SELECT id FROM students WHERE name = ?",
            ("Student B",),
        ).fetchone()["id"]

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_students (
                    tenant_id,
                    student_id
                )
                VALUES (?, ?)
                """,
                ("school-A", student_id),
            )

    finally:
        connection.close()
