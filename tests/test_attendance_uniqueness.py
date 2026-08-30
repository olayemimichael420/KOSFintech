import sqlite3

import pytest


def create_schema(connection):
    connection.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE UNIQUE INDEX ux_students_id_tenant
        ON students(id, tenant_id)
    """)

    connection.execute("""
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            remark TEXT,
            FOREIGN KEY (student_id, tenant_id)
                REFERENCES students(id, tenant_id),
            UNIQUE (tenant_id, student_id, attendance_date)
        )
    """)

    connection.commit()


def test_student_can_have_only_one_attendance_record_per_day():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        create_schema(connection)

        connection.execute(
            """
            INSERT INTO students (tenant_id, name)
            VALUES (?, ?)
            """,
            ("school-001", "Student One"),
        )

        student_id = connection.execute(
            "SELECT id FROM students"
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO attendance (
                tenant_id,
                student_id,
                attendance_date,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            ("school-001", student_id, "2026-08-29", "present"),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO attendance (
                    tenant_id,
                    student_id,
                    attendance_date,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                ("school-001", student_id, "2026-08-29", "absent"),
            )

    finally:
        connection.close()


def test_same_student_can_have_attendance_on_different_dates():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        create_schema(connection)

        connection.execute(
            """
            INSERT INTO students (tenant_id, name)
            VALUES (?, ?)
            """,
            ("school-001", "Student One"),
        )

        student_id = connection.execute(
            "SELECT id FROM students"
        ).fetchone()[0]

        for attendance_date in ("2026-08-29", "2026-08-30"):
            connection.execute(
                """
                INSERT INTO attendance (
                    tenant_id,
                    student_id,
                    attendance_date,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                ("school-001", student_id, attendance_date, "present"),
            )

        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM attendance"
        ).fetchone()[0]

        assert count == 2

    finally:
        connection.close()
