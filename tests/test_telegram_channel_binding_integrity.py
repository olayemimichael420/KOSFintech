import sqlite3

import database


def _create_administration(connection, tenant_id):
    return connection.execute(
        """
        INSERT INTO administrations (
            tenant_id,
            name,
            administration_type
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, "Test Administration", "school"),
    ).lastrowid


def test_binding_rejects_cross_tenant_administration(db_connection):
    connection = db_connection
    database.init_db()

    administration_id = _create_administration(connection, "tenant-a")

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
                "-100111222333",
                "tenant-b",
                administration_id,
                "group",
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "Cross-tenant Telegram administration binding was accepted"
        )


def test_binding_rejects_missing_administration(db_connection):
    connection = db_connection
    database.init_db()

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
                "-100444555666",
                "tenant-a",
                999999,
                "group",
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "Telegram binding accepted nonexistent administration"
        )
