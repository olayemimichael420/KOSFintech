import sqlite3
import pytest


def test_administration_authority_schema(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "authority.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'administration_authorities'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(administration_authorities)"
            ).fetchall()
        }

        assert set(columns) == {
            "id",
            "tenant_id",
            "administration_id",
            "user_id",
            "role",
            "status",
            "created_at",
        }

        assert columns["id"]["pk"] == 1

        assert columns["tenant_id"]["notnull"] == 1
        assert columns["administration_id"]["notnull"] == 1
        assert columns["user_id"]["notnull"] == 1
        assert columns["role"]["notnull"] == 1
        assert columns["status"]["notnull"] == 1

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(administration_authorities)"
        ).fetchall()

        relationships = {
            (
                row["from"],
                row["table"],
                row["to"],
            )
            for row in foreign_keys
        }

        assert (
            "administration_id",
            "administrations",
            "id",
        ) in relationships

        assert (
            "user_id",
            "users",
            "id",
        ) in relationships

        # The tenant-boundary foreign keys are composite.
        composite_relationships = {
            (
                row["id"],
                row["from"],
                row["table"],
                row["to"],
            )
            for row in foreign_keys
        }

        administration_fk = [
            row
            for row in foreign_keys
            if row["table"] == "administrations"
        ]

        user_fk = [
            row
            for row in foreign_keys
            if row["table"] == "users"
        ]

        assert len(administration_fk) == 2
        assert len(user_fk) == 2

        assert {
            row["from"]
            for row in administration_fk
        } == {
            "administration_id",
            "tenant_id",
        }

        assert {
            row["from"]
            for row in user_fk
        } == {
            "user_id",
            "tenant_id",
        }

        # Verify that the database actually rejects
        # a cross-tenant authority assignment.
        connection.execute(
            """
            INSERT INTO administrations (
                tenant_id,
                name,
                administration_type
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-001",
                "Tenant One",
                "school",
            ),
        )

        connection.execute(
            """
            INSERT INTO users (
                tenant_id,
                name,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-002",
                "Tenant Two User",
                "member",
            ),
        )

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO administration_authorities (
                    tenant_id,
                    administration_id,
                    user_id,
                    role
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    1,
                    1,
                    "owner",
                ),
            )

    finally:
        connection.close()
