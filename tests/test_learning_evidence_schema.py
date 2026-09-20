import database


def _connection():
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_learning_evidence_table_exists_with_expected_columns():
    connection = _connection()

    try:
        columns = connection.execute(
            "PRAGMA table_info(learning_evidence)"
        ).fetchall()

        assert [row["name"] for row in columns] == [
            "id",
            "tenant_id",
            "membership_id",
            "teaching_content_id",
            "evidence_date",
            "description",
            "remark",
        ]
    finally:
        connection.close()


def test_learning_evidence_has_tenant_scoped_foreign_keys():
    connection = _connection()

    try:
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(learning_evidence)"
        ).fetchall()

        targets = {
            (row["table"], row["from"], row["to"])
            for row in foreign_keys
        }

        assert (
            "memberships",
            "membership_id",
            "id",
        ) in targets

        assert (
            "teaching_contents",
            "teaching_content_id",
            "id",
        ) in targets

        assert (
            "memberships",
            "tenant_id",
            "tenant_id",
        ) in targets

        assert (
            "teaching_contents",
            "tenant_id",
            "tenant_id",
        ) in targets
    finally:
        connection.close()


def test_learning_evidence_has_tenant_scoped_identity_index():
    connection = _connection()

    try:
        indexes = connection.execute(
            "PRAGMA index_list(learning_evidence)"
        ).fetchall()

        names = {row["name"] for row in indexes}

        assert "ux_learning_evidence_id_tenant" in names

        index_columns = connection.execute(
            "PRAGMA index_info(ux_learning_evidence_id_tenant)"
        ).fetchall()

        assert [row["name"] for row in index_columns] == [
            "id",
            "tenant_id",
        ]
    finally:
        connection.close()
