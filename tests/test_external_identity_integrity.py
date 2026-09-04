import sqlite3

import database


def _create_user(connection, tenant_id, name="Test User"):
    cursor = connection.execute(
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
            tenant_id,
            name,
            None,
            "member",
            "active",
        ),
    )
    connection.commit()
    return cursor.lastrowid


def test_external_identity_can_reference_canonical_user(db_connection):
    connection = db_connection
    try:
        database.init_db()

        user_id = _create_user(connection, "tenant-a")

        connection.execute(
            """
            INSERT INTO external_identities (
                provider,
                subject,
                tenant_id,
                user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            ("telegram", "telegram-user-001", "tenant-a", user_id),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT provider, subject, tenant_id, user_id
            FROM external_identities
            WHERE provider = ?
              AND subject = ?
            """,
            ("telegram", "telegram-user-001"),
        ).fetchone()

        assert row["tenant_id"] == "tenant-a"
        assert row["user_id"] == user_id
    finally:
        connection.close()


def test_external_identity_rejects_duplicate_provider_subject(db_connection):
    connection = db_connection
    try:
        database.init_db()

        user_id = _create_user(connection, "tenant-a")

        connection.execute(
            """
            INSERT INTO external_identities (
                provider,
                subject,
                tenant_id,
                user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            ("telegram", "telegram-user-002", "tenant-a", user_id),
        )

        try:
            connection.execute(
                """
                INSERT INTO external_identities (
                    provider,
                    subject,
                    tenant_id,
                    user_id
                )
                VALUES (?, ?, ?, ?)
                """,
                ("telegram", "telegram-user-002", "tenant-a", user_id),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(
                "Duplicate provider/subject was accepted"
            )
    finally:
        connection.close()


def test_external_identity_rejects_cross_tenant_user_binding(db_connection):
    connection = db_connection
    try:
        database.init_db()

        user_id = _create_user(connection, "tenant-a")

        try:
            connection.execute(
                """
                INSERT INTO external_identities (
                    provider,
                    subject,
                    tenant_id,
                    user_id
                )
                VALUES (?, ?, ?, ?)
                """,
                ("telegram", "telegram-user-003", "tenant-b", user_id),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(
                "Cross-tenant external identity binding was accepted"
            )
    finally:
        connection.close()
