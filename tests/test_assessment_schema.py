import database


def _connection():
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_assessment_table_exists_with_expected_columns():
    connection = _connection()
    try:
        columns = connection.execute(
            "PRAGMA table_info(assessments)"
        ).fetchall()

        assert [row["name"] for row in columns] == [
            "id",
            "tenant_id",
            "teaching_content_id",
            "name",
            "description",
            "assessment_date",
            "status",
        ]
    finally:
        connection.close()


def test_assessment_has_tenant_scoped_foreign_keys():
    connection = _connection()
    try:
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(assessments)"
        ).fetchall()

        targets = {
            (row["table"], row["from"], row["to"])
            for row in foreign_keys
        }

        assert ("tenants", "tenant_id", "tenant_id") in targets
        assert (
            "teaching_contents",
            "teaching_content_id",
            "id",
        ) in targets
        assert (
            "teaching_contents",
            "tenant_id",
            "tenant_id",
        ) in targets
    finally:
        connection.close()


def test_assessment_has_tenant_scoped_identity_index():
    connection = _connection()
    try:
        indexes = connection.execute(
            "PRAGMA index_list(assessments)"
        ).fetchall()

        names = {row["name"] for row in indexes}
        assert "ux_assessments_id_tenant" in names

        index_columns = connection.execute(
            "PRAGMA index_info(ux_assessments_id_tenant)"
        ).fetchall()

        assert [row["name"] for row in index_columns] == [
            "id",
            "tenant_id",
        ]
    finally:
        connection.close()


def test_assessment_name_is_unique_within_content_and_tenant():
    connection = _connection()
    try:
        unique_indexes = connection.execute(
            "PRAGMA index_list(assessments)"
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
                "teaching_content_id",
                "name",
            ]:
                found = True
                break

        assert found
    finally:
        connection.close()
