import pytest
import sqlite3

import database


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()


def _create_user(connection, tenant_id, name):
    cursor = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, name, "member"),
    )
    connection.commit()
    return cursor.lastrowid


def test_service_acts_table_exists(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'service_acts'
            """
        ).fetchone()

        assert row is not None
        assert row["name"] == "service_acts"
    finally:
        connection.close()


def test_service_act_requires_valid_users_in_same_tenant(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(connection, "tenant-a", "Provider")
        recipient = _create_user(connection, "tenant-a", "Recipient")

        connection.execute(
            """
            INSERT INTO service_acts (
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-a",
                provider,
                recipient,
                "Tutoring",
                "Mathematics tutoring",
            ),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT tenant_id, provider_user_id, recipient_user_id, status
            FROM service_acts
            """
        ).fetchone()

        assert row["tenant_id"] == "tenant-a"
        assert row["provider_user_id"] == provider
        assert row["recipient_user_id"] == recipient
        assert row["status"] == "created"
    finally:
        connection.close()


def test_service_act_rejects_cross_tenant_provider(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        provider = _create_user(connection, "tenant-a", "Provider")
        recipient = _create_user(connection, "tenant-b", "Recipient")

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO service_acts (
                    tenant_id,
                    provider_user_id,
                    recipient_user_id,
                    title,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "tenant-b",
                    provider,
                    recipient,
                    "Invalid Act",
                    "Cross-tenant relationship",
                ),
            )
    finally:
        connection.close()


def test_service_act_rejects_self_service(
    tmp_path,
    monkeypatch,
):
    connection = _setup_fresh_db(tmp_path, monkeypatch)

    try:
        user_id = _create_user(connection, "tenant-a", "User")

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO service_acts (
                    tenant_id,
                    provider_user_id,
                    recipient_user_id,
                    title,
                    description
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "tenant-a",
                    user_id,
                    user_id,
                    "Self Service",
                    "Should not be permitted",
                ),
            )
    finally:
        connection.close()
