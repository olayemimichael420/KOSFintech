import sqlite3

import database


def test_j6b_judicial_recusal_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "judicial_recusal.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'judicial_recusals'
            """
        ).fetchone()

        assert table is not None

        expected_columns = {
            "id",
            "tenant_id",
            "judicial_authority_id",
            "jurisdiction_id",
            "proceeding_id",
            "scope",
            "reason",
            "initiated_by",
            "recorded_at",
            "resolved_at",
            "status",
        }

        actual_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(judicial_recusals)"
            ).fetchall()
        }

        assert actual_columns == expected_columns

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(judicial_recusals)"
        ).fetchall()

        actual_fk_targets = {
            row["table"]
            for row in foreign_keys
        }

        expected_fk_targets = {
            "judicial_authorities",
            "judicial_jurisdictions",
            "judicial_proceedings",
            "users",
        }

        assert actual_fk_targets == expected_fk_targets

        indexes = {
            row["name"]
            for row in connection.execute(
                "PRAGMA index_list(judicial_recusals)"
            ).fetchall()
        }

        expected_indexes = {
            "ix_judicial_recusals_tenant_status",
            "ix_judicial_recusals_tenant_authority",
            "ix_judicial_recusals_tenant_jurisdiction",
            "ix_judicial_recusals_tenant_proceeding",
        }

        assert expected_indexes.issubset(indexes)

        table_sql = table["sql"].lower()

        assert "check(scope in" in table_sql
        assert "unique(id, tenant_id)" in table_sql

        scope_check = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'judicial_recusals'
            """
        ).fetchone()["sql"].lower()

        assert "jurisdiction" in scope_check
        assert "proceeding" in scope_check
        assert "active" in scope_check
        assert "resolved" in scope_check

    finally:
        connection.close()
