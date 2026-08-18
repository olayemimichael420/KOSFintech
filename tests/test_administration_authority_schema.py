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
            "administration_id",
            "user_id",
            "role",
            "status",
            "created_at",
        }

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(administration_authorities)"
        ).fetchall()

        relationships = {
            (row["from"], row["table"], row["to"])
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

    finally:
        connection.close()
