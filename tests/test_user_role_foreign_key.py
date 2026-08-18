import sqlite3

import pytest
import database


def test_user_roles_enforce_user_and_role_foreign_keys(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "foreign_key.db"

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
                "test@example.com",
                "teacher",
                "active",
            ),
        )

        user_id = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            ("test@example.com",),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO roles (
                tenant_id,
                name,
                description,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "school-001",
                "teacher",
                "Teaching staff",
                "active",
            ),
        )

        role_id = connection.execute(
            "SELECT id FROM roles WHERE name = ?",
            ("teacher",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO user_roles (
                tenant_id,
                user_id,
                role_id
            )
            VALUES (?, ?, ?)
            """,
            ("school-001", user_id, role_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, user_id, role_id
            FROM user_roles
            WHERE user_id = ?
              AND role_id = ?
            """,
            (user_id, role_id),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO user_roles (
                    tenant_id,
                    user_id,
                    role_id
                )
                VALUES (?, ?, ?)
                """,
                ("school-001", 999999, role_id),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO user_roles (
                    tenant_id,
                    user_id,
                    role_id
                )
                VALUES (?, ?, ?)
                """,
                ("school-001", user_id, 999999),
            )

    finally:
        connection.close()
