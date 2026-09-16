import database


def test_institution_anchor_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'institution_anchors'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(institution_anchors)"
            ).fetchall()
        }

        assert set(columns) == {
            "id",
            "institution_type",
            "name",
            "provenance_reference",
            "verification_status",
            "status",
            "created_at",
        }

        assert columns["id"]["pk"] == 1

        for column in (
            "institution_type",
            "name",
            "provenance_reference",
            "verification_status",
            "status",
        ):
            assert columns[column]["notnull"] == 1

        assert "tenant_id" not in columns

        connection.execute(
            """
            INSERT INTO institution_anchors (
                institution_type,
                name,
                provenance_reference
            )
            VALUES (?, ?, ?)
            """,
            (
                "church",
                "Example Church",
                "official-reference",
            ),
        )

        row = connection.execute(
            """
            SELECT
                institution_type,
                name,
                provenance_reference,
                verification_status,
                status
            FROM institution_anchors
            WHERE name = ?
            """,
            ("Example Church",),
        ).fetchone()

        assert row["institution_type"] == "church"
        assert row["name"] == "Example Church"
        assert row["provenance_reference"] == "official-reference"
        assert row["verification_status"] == "pending"
        assert row["status"] == "active"

        try:
            connection.execute(
                """
                INSERT INTO institution_anchors (
                    institution_type,
                    name,
                    provenance_reference,
                    verification_status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "church",
                    "Invalid Verification Church",
                    "reference",
                    "invalid",
                ),
            )
            assert False, "invalid verification_status was accepted"
        except Exception:
            pass

        try:
            connection.execute(
                """
                INSERT INTO institution_anchors (
                    institution_type,
                    name,
                    provenance_reference,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "church",
                    "Invalid Status Church",
                    "reference",
                    "invalid",
                ),
            )
            assert False, "invalid status was accepted"
        except Exception:
            pass

    finally:
        connection.close()
