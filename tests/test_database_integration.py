import sqlite3

import database


def test_init_db_creates_core_schema(monkeypatch, tmp_path):
    db_path = tmp_path / "integration.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()

    connection = sqlite3.connect(db_path)

    try:
        connection.row_factory = sqlite3.Row

        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        expected_tables = {
            "schema_meta",
            "schools",
            "students",
            "teachers",
            "parents",
            "parent_schools",
            "school_students",
            "teacher_students",
            "school_teachers",
            "users",
            "user_schools",
            "roles",
            "user_roles",
            "permissions",
            "role_permissions",
        }

        assert expected_tables.issubset(tables)

    finally:
        connection.close()
