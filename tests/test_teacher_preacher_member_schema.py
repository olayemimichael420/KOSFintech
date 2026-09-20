import sqlite3

import pytest

import database


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "teacher_preacher_member.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )


def _seed_person(connection, name):
    cursor = connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (name,),
    )
    return cursor.lastrowid


def _seed_church_anchor(connection, tenant_id, name):
    cursor = connection.execute(
        """
        INSERT INTO church_anchors (
            tenant_id,
            name,
            provenance_reference
        )
        VALUES (?, ?, ?)
        """,
        (
            tenant_id,
            name,
            "test",
        ),
    )
    return cursor.lastrowid


def _seed_teacher_preacher(connection, tenant_id, person_id):
    cursor = connection.execute(
        """
        INSERT INTO teacher_preachers (
            tenant_id,
            person_id,
            role
        )
        VALUES (?, ?, 'teacher')
        """,
        (tenant_id, person_id),
    )
    return cursor.lastrowid


def _seed_membership(connection, tenant_id, person_id, church_anchor_id):
    cursor = connection.execute(
        """
        INSERT INTO memberships (
            tenant_id,
            person_id,
            church_anchor_id,
            provenance_reference
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            tenant_id,
            person_id,
            church_anchor_id,
            "test",
        ),
    )
    return cursor.lastrowid


def test_teacher_preacher_member_accepts_valid_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    try:
        _seed_tenant(connection, "tenant-cmos")

        teacher_person_id = _seed_person(connection, "Teacher")
        member_person_id = _seed_person(connection, "Member")

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-cmos",
            "Church",
        )

        teacher_preacher_id = _seed_teacher_preacher(
            connection,
            "tenant-cmos",
            teacher_person_id,
        )

        membership_id = _seed_membership(
            connection,
            "tenant-cmos",
            member_person_id,
            anchor_id,
        )

        connection.execute(
            """
            INSERT INTO teacher_preacher_members (
                tenant_id,
                teacher_preacher_id,
                membership_id
            )
            VALUES (?, ?, ?)
            """,
            (
                "tenant-cmos",
                teacher_preacher_id,
                membership_id,
            ),
        )
    finally:
        connection.close()


def test_teacher_preacher_member_rejects_invalid_teacher_preacher(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    try:
        _seed_tenant(connection, "tenant-cmos")

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teacher_preacher_members (
                    tenant_id,
                    teacher_preacher_id,
                    membership_id
                )
                VALUES (?, ?, ?)
                """,
                ("tenant-cmos", 999999, 999999),
            )
    finally:
        connection.close()


def test_teacher_preacher_member_rejects_cross_tenant_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    try:
        _seed_tenant(connection, "tenant-a")
        _seed_tenant(connection, "tenant-b")

        teacher_person_id = _seed_person(connection, "Teacher")
        member_person_id = _seed_person(connection, "Member")

        anchor_b = _seed_church_anchor(
            connection,
            "tenant-b",
            "Church B",
        )

        teacher_preacher_id = _seed_teacher_preacher(
            connection,
            "tenant-a",
            teacher_person_id,
        )

        membership_id = _seed_membership(
            connection,
            "tenant-b",
            member_person_id,
            anchor_b,
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teacher_preacher_members (
                    tenant_id,
                    teacher_preacher_id,
                    membership_id
                )
                VALUES (?, ?, ?)
                """,
                (
                    "tenant-a",
                    teacher_preacher_id,
                    membership_id,
                ),
            )
    finally:
        connection.close()


def test_teacher_preacher_member_rejects_duplicate_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    try:
        _seed_tenant(connection, "tenant-cmos")

        teacher_person_id = _seed_person(connection, "Teacher")
        member_person_id = _seed_person(connection, "Member")

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-cmos",
            "Church",
        )

        teacher_preacher_id = _seed_teacher_preacher(
            connection,
            "tenant-cmos",
            teacher_person_id,
        )

        membership_id = _seed_membership(
            connection,
            "tenant-cmos",
            member_person_id,
            anchor_id,
        )

        values = (
            "tenant-cmos",
            teacher_preacher_id,
            membership_id,
        )

        connection.execute(
            """
            INSERT INTO teacher_preacher_members (
                tenant_id,
                teacher_preacher_id,
                membership_id
            )
            VALUES (?, ?, ?)
            """,
            values,
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teacher_preacher_members (
                    tenant_id,
                    teacher_preacher_id,
                    membership_id
                )
                VALUES (?, ?, ?)
                """,
                values,
            )
    finally:
        connection.close()
