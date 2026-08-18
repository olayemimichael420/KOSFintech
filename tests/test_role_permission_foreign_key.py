import sqlite3

import pytest

import database


def test_role_permissions_enforce_foreign_keys(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "role_permission_fk.db"

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

        connection.execute(
            """
            INSERT INTO permissions (
                tenant_id,
                name,
                description,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "school-001",
                "student.read",
                "View student records",
                "active",
            ),
        )

        permission_id = connection.execute(
            "SELECT id FROM permissions WHERE name = ?",
            ("student.read",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id,
                role_id,
                permission_id
            )
            VALUES (?, ?, ?)
            """,
            ("school-001", role_id, permission_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, role_id, permission_id
            FROM role_permissions
            WHERE role_id = ?
              AND permission_id = ?
            """,
            (role_id, permission_id),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO role_permissions (
                    tenant_id,
                    role_id,
                    permission_id
                )
                VALUES (?, ?, ?)
                """,
                ("school-001", 999999, permission_id),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO role_permissions (
                    tenant_id,
                    role_id,
                    permission_id
                )
                VALUES (?, ?, ?)
                """,
                ("school-001", role_id, 999999),
            )

    finally:
        connection.close()
