import sqlite3

import pytest

import database


def test_parent_students_enforce_same_tenant(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "parent_student_tenant_fk.db"

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
            INSERT INTO parents (
                tenant_id,
                user_id,
                name,
                phone,
                email,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "school-A",
                None,
                "Parent A",
                None,
                None,
                "active",
            ),
        )

        parent_id = connection.execute(
            "SELECT id FROM parents WHERE name = ?",
            ("Parent A",),
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
                "school-A",
                None,
                "Student A",
                "JSS 1",
                12,
                None,
                None,
                "active",
            ),
        )

        student_id = connection.execute(
            "SELECT id FROM students WHERE name = ?",
            ("Student A",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO parent_students (
                tenant_id,
                parent_id,
                student_id
            )
            VALUES (?, ?, ?)
            """,
            ("school-A", parent_id, student_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, parent_id, student_id
            FROM parent_students
            WHERE tenant_id = ?
              AND parent_id = ?
              AND student_id = ?
            """,
            ("school-A", parent_id, student_id),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO parent_students (
                    tenant_id,
                    parent_id,
                    student_id
                )
                VALUES (?, ?, ?)
                """,
                ("school-B", parent_id, student_id),
            )

    finally:
        connection.close()
