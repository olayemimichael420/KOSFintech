import sqlite3

import pytest

import database


def test_parent_schools_enforce_parent_foreign_key(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "parent_school_fk.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()

    connection = database.get_connection()

    try:
        connection.execute(
            """
            INSERT INTO parents (
                tenant_id,
                user_id,
                name,
                phone,
                email,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "school-001",
                None,
                "Test Parent",
                "08000000000",
                "parent@example.com",
                "active",
            ),
        )

        parent_id = connection.execute(
            "SELECT id FROM parents WHERE name = ?",
            ("Test Parent",),
        ).fetchone()["id"]

        connection.commit()

        connection.execute(
            """
            INSERT INTO parent_schools (
                tenant_id,
                parent_id
            )
            VALUES (?, ?)
            """,
            ("school-001", parent_id),
        )

        connection.commit()

        valid = connection.execute(
            """
            SELECT tenant_id, parent_id
            FROM parent_schools
            WHERE parent_id = ?
            """,
            (parent_id,),
        ).fetchone()

        assert valid is not None

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO parent_schools (
                    tenant_id,
                    parent_id
                )
                VALUES (?, ?)
                """,
                ("school-001", 999999),
            )

    finally:
        connection.close()
