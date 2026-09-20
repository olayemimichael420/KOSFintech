import sqlite3

import database
import pytest

from models.teaching_session_member import TeachingSessionMemberLink
from repositories.teaching_session_member_repository import (
    TeachingSessionMemberRepository,
)


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "teaching_session_member_repository.db"

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


def _seed_teaching_session(connection, tenant_id, name):
    cursor = connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            tenant_id,
            name,
            "2026-01-01",
            "2026-03-31",
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

        member_person_id = _seed_person(
            connection,
            "Member",
        )

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-cmos",
            "Church",
        )

        membership_id = _seed_membership(
            connection,
            "tenant-cmos",
            member_person_id,
            anchor_id,
        )

        teaching_session_id = _seed_teaching_session(
            connection,
            "tenant-cmos",
            "Session",
        )

        repository = TeachingSessionMemberRepository(connection)

        link = TeachingSessionMemberLink(
            tenant_id="tenant-cmos",
            teaching_session_id=teaching_session_id,
            membership_id=membership_id,
        )

        created = repository.create(link)

        assert created == link

        found = repository.get(
            "tenant-cmos",
            teaching_session_id,
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

        member_person_id = _seed_person(
            connection,
            "Member",
        )

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-a",
            "Church A",
        )

        membership_id = _seed_membership(
            connection,
            "tenant-a",
            member_person_id,
            anchor_id,
        )

        teaching_session_id = _seed_teaching_session(
            connection,
            "tenant-a",
            "Session A",
        )

        repository = TeachingSessionMemberRepository(connection)

        link = TeachingSessionMemberLink(
            tenant_id="tenant-a",
            teaching_session_id=teaching_session_id,
            membership_id=membership_id,
        )

        repository.create(link)

        assert repository.get(
            "tenant-a",
            teaching_session_id,
            membership_id,
        ) == link

        assert repository.get(
            "tenant-b",
            teaching_session_id,
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

        member_person_id = _seed_person(
            connection,
            "Member",
        )

        anchor_id = _seed_church_anchor(
            connection,
            "tenant-cmos",
            "Church",
        )

        membership_id = _seed_membership(
            connection,
            "tenant-cmos",
            member_person_id,
            anchor_id,
        )

        teaching_session_id = _seed_teaching_session(
            connection,
            "tenant-cmos",
            "Session",
        )

        repository = TeachingSessionMemberRepository(connection)

        link = TeachingSessionMemberLink(
            tenant_id="tenant-cmos",
            teaching_session_id=teaching_session_id,
            membership_id=membership_id,
        )

        repository.create(link)

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(link)
    finally:
        connection.close()
