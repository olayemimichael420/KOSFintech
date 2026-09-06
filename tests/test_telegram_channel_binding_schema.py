import sqlite3

import database


def test_telegram_channel_bindings_schema(db_connection):
    connection = db_connection

    database.init_db()

    table = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'telegram_channel_bindings'
        """
    ).fetchone()

    assert table is not None

    columns = {
        row["name"]: row
        for row in connection.execute(
            "PRAGMA table_info(telegram_channel_bindings)"
        ).fetchall()
    }

    assert set(columns) == {
        "id",
        "provider",
        "chat_id",
        "tenant_id",
        "administration_id",
        "binding_type",
        "status",
        "created_at",
    }

    assert columns["id"]["pk"] == 1
    assert columns["provider"]["notnull"] == 1
    assert columns["chat_id"]["notnull"] == 1
    assert columns["tenant_id"]["notnull"] == 1
    assert columns["administration_id"]["notnull"] == 1
    assert columns["binding_type"]["notnull"] == 1
    assert columns["status"]["notnull"] == 1


def test_telegram_channel_binding_rejects_duplicate_chat(db_connection):
    connection = db_connection

    database.init_db()

    administration_id = connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        ("tenant-a", "Test Administration", "school"),
    ).lastrowid

    connection.execute(
        """
        INSERT INTO telegram_channel_bindings (
            provider,
            chat_id,
            tenant_id,
            administration_id,
            binding_type
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "telegram",
            "-100123456789",
            "tenant-a",
            administration_id,
            "supergroup",
        ),
    )
    connection.commit()

    try:
        connection.execute(
            """
            INSERT INTO telegram_channel_bindings (
                provider,
                chat_id,
                tenant_id,
                administration_id,
                binding_type
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "telegram",
                "-100123456789",
                "tenant-a",
                administration_id,
                "supergroup",
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("Duplicate Telegram chat binding was accepted")
