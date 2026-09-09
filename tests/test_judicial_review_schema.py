import database


def test_j7b_judicial_review_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "judicial_review.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        table = connection.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'judicial_reviews'
            """
        ).fetchone()

        assert table is not None

        expected_columns = {
            "id",
            "tenant_id",
            "proceeding_id",
            "decision_id",
            "originating_judicial_authority_id",
            "jurisdiction_id",
            "review_type",
            "initiated_by",
            "grounds",
            "status",
            "recorded_at",
        }

        actual_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(judicial_reviews)"
            ).fetchall()
        }

        assert actual_columns == expected_columns

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(judicial_reviews)"
        ).fetchall()

        actual_fk_targets = {
            row["table"]
            for row in foreign_keys
        }

        expected_fk_targets = {
            "judicial_proceedings",
            "judicial_decisions",
            "judicial_authorities",
            "judicial_jurisdictions",
            "users",
        }

        assert actual_fk_targets == expected_fk_targets

        indexes = {
            row["name"]
            for row in connection.execute(
                "PRAGMA index_list(judicial_reviews)"
            ).fetchall()
        }

        expected_indexes = {
            "ix_judicial_reviews_tenant_proceeding",
            "ix_judicial_reviews_tenant_decision",
            "ix_judicial_reviews_tenant_authority",
            "ix_judicial_reviews_tenant_jurisdiction",
            "ix_judicial_reviews_tenant_status",
        }

        assert expected_indexes.issubset(indexes)

        table_sql = table["sql"].lower()

        assert "check(review_type in" in table_sql
        assert "'review'" in table_sql
        assert "'appeal'" in table_sql
        assert "check(status in" in table_sql
        assert "'proposed'" in table_sql
        assert "unique(id, tenant_id)" in table_sql

    finally:
        connection.close()
