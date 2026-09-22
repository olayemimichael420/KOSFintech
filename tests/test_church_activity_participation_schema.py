import database


def test_church_activity_participation_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "church_activity_participation_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'church_activity_participations'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(church_activity_participations)"
            ).fetchall()
        }

        assert set(columns) == {
            "tenant_id",
            "church_activity_id",
            "membership_id",
        }

        assert all(
            columns[column]["notnull"] == 1
            for column in columns
        )

        primary_key = sorted(
            (
                row["pk"],
                row["name"],
            )
            for row in columns.values()
            if row["pk"] > 0
        )

        assert primary_key == [
            (1, "tenant_id"),
            (2, "church_activity_id"),
            (3, "membership_id"),
        ]

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(church_activity_participations)"
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
            "church_activity_id",
            "church_activities",
            "id",
        ) in relationships

        assert (
            "membership_id",
            "memberships",
            "id",
        ) in relationships

    finally:
        connection.close()
