import sqlite3
import pytest


def test_administrations_schema(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "administrations.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()

    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'administrations'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(administrations)"
            ).fetchall()
        }

        assert set(columns) == {
            "id",
            "tenant_id",
            "name",
            "administration_type",
            "status",
            "created_at",
        }

        assert columns["id"]["pk"] == 1
        assert columns["tenant_id"]["notnull"] == 1
        assert columns["name"]["notnull"] == 1
        assert columns["administration_type"]["notnull"] == 1
        assert columns["status"]["notnull"] == 1

        connection.execute(
            """
            INSERT INTO administrations (
                tenant_id,
                name,
                administration_type
            )
            VALUES (?, ?, ?)
            """,
            ("tenant-001", "Example School", "school"),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                tenant_id,
                name,
                administration_type,
                status
            FROM administrations
            WHERE tenant_id = ?
            """,
            ("tenant-001",),
        ).fetchone()

        assert row is not None
        assert row["name"] == "Example School"
        assert row["administration_type"] == "school"
        assert row["status"] == "active"

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO administrations (
                    tenant_id,
                    name,
                    administration_type
                )
                VALUES (?, ?, ?)
                """,
                ("tenant-001", "Duplicate", "school"),
            )

    finally:
        connection.close()
