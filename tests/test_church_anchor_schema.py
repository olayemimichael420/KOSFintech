import sqlite3
import pytest


def test_church_anchors_schema(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "church_anchor_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'church_anchors'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(church_anchors)"
            ).fetchall()
        }

        assert set(columns) == {
            "id",
            "tenant_id",
            "name",
            "provenance_reference",
            "verification_status",
            "status",
            "created_at",
        }

        assert columns["id"]["pk"] == 1

        for column in (
            "tenant_id",
            "name",
            "provenance_reference",
            "verification_status",
            "status",
        ):
            assert columns[column]["notnull"] == 1

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(church_anchors)"
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
            "tenant_id",
            "administrations",
            "tenant_id",
        ) in relationships

        connection.execute(
            """
            INSERT INTO administrations (
                tenant_id,
                name,
                administration_type
            )
            VALUES (?, ?, ?)
            """,
            ("tenant-001", "Example Church Administration", "church"),
        )

        connection.execute(
            """
            INSERT INTO church_anchors (
                tenant_id,
                name,
                provenance_reference
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-001",
                "Example Church",
                "official-reference",
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status
            FROM church_anchors
            WHERE tenant_id = ?
            """,
            ("tenant-001",),
        ).fetchone()

        assert row is not None
        assert row["name"] == "Example Church"
        assert row["provenance_reference"] == "official-reference"
        assert row["verification_status"] == "pending"
        assert row["status"] == "active"

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO church_anchors (
                    tenant_id,
                    name,
                    provenance_reference
                )
                VALUES (?, ?, ?)
                """,
                (
                    "tenant-999",
                    "Unbound Church",
                    "unverified-reference",
                ),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO church_anchors (
                    tenant_id,
                    name,
                    provenance_reference,
                    verification_status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "tenant-001",
                    "Invalid Status Church",
                    "reference",
                    "invalid",
                ),
            )

    finally:
        connection.close()
