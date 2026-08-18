import sqlite3

import pytest

import database


def test_user_schools_enforce_user_foreign_key(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "user_school_fk.db"

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
            INSERT INTO users (
                tenant_id,
                name,
                email,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-001",
                "Test User",
                "user@example.com",
                "teacher",
                "active",
            ),
        )

        user_id = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            ("user@example.com",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO user_schools (
                tenant_id,
                user_id
            )
            VALUES (?, ?)
            """,
            ("school-001", user_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, user_id
            FROM user_schools
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO user_schools (
                    tenant_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                ("school-001", 999999),
            )

    finally:
        connection.close()
