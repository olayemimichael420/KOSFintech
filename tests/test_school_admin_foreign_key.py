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
