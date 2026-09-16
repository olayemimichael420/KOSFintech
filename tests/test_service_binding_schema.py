import database


def test_service_bindings_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_schema.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'service_bindings'
            """
        ).fetchone()

        assert table is not None

        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(service_bindings)"
            ).fetchall()
        }

        assert set(columns) == {
            "id",
            "institution_anchor_id",
            "tenant_id",
            "status",
            "created_at",
        }

        assert columns["id"]["pk"] == 1

        for column in (
            "institution_anchor_id",
            "tenant_id",
            "status",
        ):
            assert columns[column]["notnull"] == 1

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(service_bindings)"
        ).fetchall()

        assert any(
            row["table"] == "institution_anchors"
            and row["from"] == "institution_anchor_id"
            and row["to"] == "id"
            for row in foreign_keys
        )

        assert "authority" not in columns
        assert "role" not in columns
        assert "permission" not in columns
        assert "user_id" not in columns
        assert "administration_id" not in columns

    finally:
        connection.close()
