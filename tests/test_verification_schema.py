import sqlite3

import database
import pytest


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "verification_fk.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()


def test_verification_table_exists(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'verifications'
            """
        ).fetchone()

        assert row is not None
    finally:
        connection.close()


def test_verification_requires_valid_service_act(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO verifications (
                    tenant_id,
                    service_act_id,
                    verifier_user_id,
                    decision
                )
                VALUES (?, ?, ?, ?)
                """,
                ("tenant-001", 999999, 999999, "approved"),
            )
    finally:
        connection.close()


def test_verification_decision_constraint(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO verifications (
                    tenant_id,
                    service_act_id,
                    verifier_user_id,
                    decision
                )
                VALUES (?, ?, ?, ?)
                """,
                ("tenant-001", 999999, 999999, "invalid"),
            )
    finally:
        connection.close()
