import sqlite3

import database
import pytest

from models.teacher_preacher_member import TeacherPreacherMemberLink
from repositories.teacher_preacher_member_repository import (
    TeacherPreacherMemberRepository,
)


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "teacher_preacher_member_repository.db"

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
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        (tenant_id,),
    )
    connection.commit()


def _seed_person(connection, name):
    cursor = connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (name,),
    )
    connection.commit()
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
        (tenant_id, name, "test"),
    )
    connection.commit()
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
    connection.commit()
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
    connection.commit()
    return cursor.lastrowid


def test_repository_create_and_get(
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

        repository = TeacherPreacherMemberRepository(connection)

        link = TeacherPreacherMemberLink(
            tenant_id="tenant-cmos",
            teacher_preacher_id=teacher_preacher_id,
            membership_id=membership_id,
        )

        created = repository.create(link)

        assert created == link

        found = repository.get(
            "tenant-cmos",
            teacher_preacher_id,
            membership_id,
        )

        assert found == link
    finally:
        connection.close()


def test_repository_get_is_tenant_scoped(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    try:
        _seed_tenant(connection, "tenant-a")
        _seed_tenant(connection, "tenant-b")

        teacher_person_id = _seed_person(connection, "Teacher")
        member_person_id = _seed_person(connection, "Member")

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-a",
            "Church A",
        )

        teacher_preacher_id = _seed_teacher_preacher(
            connection,
            "tenant-a",
            teacher_person_id,
        )

        membership_id = _seed_membership(
            connection,
            "tenant-a",
            member_person_id,
            anchor_id,
        )

        repository = TeacherPreacherMemberRepository(connection)

        link = TeacherPreacherMemberLink(
            tenant_id="tenant-a",
            teacher_preacher_id=teacher_preacher_id,
            membership_id=membership_id,
        )

        repository.create(link)

        assert repository.get(
            "tenant-a",
            teacher_preacher_id,
            membership_id,
        ) == link

        assert repository.get(
            "tenant-b",
            teacher_preacher_id,
            membership_id,
        ) is None
    finally:
        connection.close()


def test_repository_rejects_duplicate_relationship(
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

        repository = TeacherPreacherMemberRepository(connection)

        link = TeacherPreacherMemberLink(
            tenant_id="tenant-cmos",
            teacher_preacher_id=teacher_preacher_id,
            membership_id=membership_id,
        )

        repository.create(link)

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(link)
    finally:
        connection.close()
