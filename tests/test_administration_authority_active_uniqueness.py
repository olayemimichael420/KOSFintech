import sqlite3
import pytest
import database


def make_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "authority_uniqueness.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()




def seed_data(connection):
    connection.execute(
        """
        INSERT INTO administrations (tenant_id, name, administration_type)
        VALUES (?, ?, ?)
        """,
        ("tenant-a", "Administration A", "school"),
    )

    administration_id = connection.execute(
        "SELECT id FROM administrations WHERE tenant_id = ?",
        ("tenant-a",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role, status)
        VALUES (?, ?, 'member', 'active')
        """,
        ("tenant-a", "user-a"),
    )

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role, status)
        VALUES (?, ?, 'member', 'active')
        """,
        ("tenant-a", "user-b"),
    )

    user_a = connection.execute(
        "SELECT id FROM users WHERE name = ?",
        ("user-a",),
    ).fetchone()["id"]

    user_b = connection.execute(
        "SELECT id FROM users WHERE name = ?",
        ("user-b",),
    ).fetchone()["id"]

    connection.commit()

    return administration_id, user_a, user_b


def insert_authority(
    connection,
    administration_id,
    user_id,
    role="owner",
    status="active",
):
    connection.execute(
        """
        INSERT INTO administration_authorities (
            tenant_id,
            administration_id,
            user_id,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            administration_id,
            user_id,
            role,
            status,
        ),
    )
    connection.commit()


def test_only_one_active_role_per_administration(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    administration_id, user_a, user_b = seed_data(connection)

    insert_authority(
        connection,
        administration_id,
        user_a,
        role="owner",
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_authority(
            connection,
            administration_id,
            user_b,
            role="owner",
        )

    connection.close()


def test_inactive_previous_role_can_be_replaced(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    administration_id, user_a, user_b = seed_data(connection)

    insert_authority(
        connection,
        administration_id,
        user_a,
        role="owner",
        status="inactive",
    )

    insert_authority(
        connection,
        administration_id,
        user_b,
        role="owner",
        status="active",
    )

    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM administration_authorities
        WHERE administration_id = ?
          AND role = 'owner'
          AND status = 'active'
        """,
        (administration_id,),
    ).fetchone()

    assert row["count"] == 1

    connection.close()


def test_same_user_cannot_have_two_active_authority_assignments(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    administration_id, user_a, _ = seed_data(connection)

    insert_authority(
        connection,
        administration_id,
        user_a,
        role="owner",
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_authority(
            connection,
            administration_id,
            user_a,
            role="admin1",
        )

    connection.close()


def test_same_user_can_have_historical_inactive_assignments(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    administration_id, user_a, _ = seed_data(connection)

    insert_authority(
        connection,
        administration_id,
        user_a,
        role="owner",
        status="inactive",
    )

    insert_authority(
        connection,
        administration_id,
        user_a,
        role="admin1",
        status="inactive",
    )

    count = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM administration_authorities
        WHERE administration_id = ?
          AND user_id = ?
        """,
        (administration_id, user_a),
    ).fetchone()["count"]

    assert count == 2

    connection.close()
