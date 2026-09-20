import database


def _connection():
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_assessment_score_table_exists_with_expected_columns():
    connection = _connection()
    try:
        columns = connection.execute(
            "PRAGMA table_info(assessment_scores)"
        ).fetchall()

        assert [row["name"] for row in columns] == [
            "id",
            "tenant_id",
            "assessment_id",
            "membership_id",
            "score",
            "scored_date",
            "remark",
        ]
    finally:
        connection.close()


def test_assessment_score_has_tenant_scoped_foreign_keys():
    connection = _connection()
    try:
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(assessment_scores)"
        ).fetchall()

        targets = {
            (row["table"], row["from"], row["to"])
            for row in foreign_keys
        }

        assert ("tenants", "tenant_id", "tenant_id") in targets

        assert (
            "assessments",
            "assessment_id",
            "id",
        ) in targets

        assert (
            "assessments",
            "tenant_id",
            "tenant_id",
        ) in targets

        assert (
            "memberships",
            "membership_id",
            "id",
        ) in targets

        assert (
            "memberships",
            "tenant_id",
            "tenant_id",
        ) in targets
    finally:
        connection.close()


def test_assessment_score_has_tenant_scoped_identity_index():
    connection = _connection()
    try:
        indexes = connection.execute(
            "PRAGMA index_list(assessment_scores)"
        ).fetchall()

        names = {row["name"] for row in indexes}

        assert "ux_assessment_scores_id_tenant" in names

        index_columns = connection.execute(
            "PRAGMA index_info(ux_assessment_scores_id_tenant)"
        ).fetchall()

        assert [row["name"] for row in index_columns] == [
            "id",
            "tenant_id",
        ]
    finally:
        connection.close()


def test_assessment_score_is_unique_per_assessment_and_membership():
    connection = _connection()
    try:
        unique_indexes = connection.execute(
            "PRAGMA index_list(assessment_scores)"
        ).fetchall()

        found = False

        for index in unique_indexes:
            if index["unique"] != 1:
                continue

            columns = connection.execute(
                f'PRAGMA index_info("{index["name"]}")'
            ).fetchall()

            if [row["name"] for row in columns] == [
                "tenant_id",
                "assessment_id",
                "membership_id",
            ]:
                found = True
                break

        assert found
    finally:
        connection.close()
