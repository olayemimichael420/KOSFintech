import sqlite3

import pytest

import database


def test_user_schools_reject_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "user_school_cross_tenant.db"

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
                "school-B",
                "User B",
                "user-b@example.com",
                "teacher",
                "active",
            ),
        )

        user_id = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            ("user-b@example.com",),
        ).fetchone()["id"]

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO user_schools (
                    tenant_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                ("school-A", user_id),
            )

    finally:
        connection.close()
