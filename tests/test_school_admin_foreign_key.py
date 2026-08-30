import sqlite3

import database
import pytest


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "school_admin_fk.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    return database.get_connection()


def test_school_admin_user_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id,
                name,
                school_type,
                country,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-001",
                "Test School",
                "secondary",
                "Nigeria",
                "NGN",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_admins (
                    tenant_id,
                    user_id,
                    role,
                    phone
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "school-001",
                    999999,
                    "owner",
                    "08000000000",
                ),
            )
    finally:
        connection.close()



def test_school_admin_rejects_cross_tenant_user(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            INSERT INTO schools (
                tenant_id,
                name,
                school_type,
                country,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-001",
                "School One",
                "secondary",
                "Nigeria",
                "NGN",
            ),
        )

        connection.execute(
            """
            INSERT INTO schools (
                tenant_id,
                name,
                school_type,
                country,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-002",
                "School Two",
                "secondary",
                "Nigeria",
                "NGN",
            ),
        )

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
                "school-002",
                "School Two User",
                "user@school-two.test",
                "member",
                "active",
            ),
        )

        user_id = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND email = ?
            """,
            (
                "school-002",
                "user@school-two.test",
            ),
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_admins (
                    tenant_id,
                    user_id,
                    role,
                    phone
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "school-001",
                    user_id,
                    "admin1",
                    "08000000002",
                ),
            )
    finally:
        connection.close()

def test_school_admin_tenant_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO school_admins (
                    tenant_id,
                    user_id,
                    role,
                    phone
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "nonexistent-school",
                    999999,
                    "owner",
                    "08000000001",
                ),
            )
    finally:
        connection.close()
