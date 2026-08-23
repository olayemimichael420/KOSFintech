import sqlite3

import pytest

import database


def test_parent_schools_reject_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "parent_school_cross_tenant.db"

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
                "school-B",
                None,
                "Parent B",
                "08000000000",
                "parent@example.com",
                "active",
            ),
        )

        parent_id = connection.execute(
            "SELECT id FROM parents WHERE name = ?",
            ("Parent B",),
        ).fetchone()["id"]

        connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO parent_schools (
                    tenant_id,
                    parent_id
                )
                VALUES (?, ?)
                """,
                ("school-A", parent_id),
            )

    finally:
        connection.close()
