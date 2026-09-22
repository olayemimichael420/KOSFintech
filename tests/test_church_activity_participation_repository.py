import sqlite3

import pytest

import database
from models.church_activity_participation import ChurchActivityParticipation
from repositories.church_activity_participation_repository import (
    ChurchActivityParticipationRepository,
)


def _prepare_database(connection):
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        ("tenant-1",),
    )

    person_cursor = connection.execute(
        """
        INSERT INTO persons (name)
        VALUES (?)
        """,
        ("Member One",),
    )
    person_id = person_cursor.lastrowid

    connection.execute(
        """
        INSERT INTO church_anchors (
            id,
            tenant_id,
            name,
            provenance_reference
        )
        VALUES (?, ?, ?, ?)
        """,
        (1, "tenant-1", "Church One", "REF-1"),
    )

    connection.execute(
        """
        INSERT INTO memberships (
            id,
            tenant_id,
            person_id,
            church_anchor_id,
            provenance_reference
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (1, "tenant-1", person_id, 1, "MEM-1"),
    )

    connection.execute(
        """
        INSERT INTO church_activities (
            id,
            tenant_id,
            name,
            activity_type
        )
        VALUES (?, ?, ?, ?)
        """,
        (1, "tenant-1", "Activity One", "service"),
    )

    connection.commit()


def test_church_activity_participation_repository_create_get_and_lists(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "church_activity_participation_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        _prepare_database(connection)

        repository = ChurchActivityParticipationRepository(connection)

        participation = ChurchActivityParticipation(
            tenant_id="tenant-1",
            church_activity_id=1,
            membership_id=1,
        )

        assert repository.create(participation) == participation
        assert repository.get("tenant-1", 1, 1) == participation
        assert repository.get("tenant-2", 1, 1) is None
        assert repository.list_by_activity("tenant-1", 1) == [participation]
        assert repository.list_by_member("tenant-1", 1) == [participation]
        assert repository.list_by_activity("tenant-2", 1) == []
        assert repository.list_by_member("tenant-2", 1) == []

    finally:
        connection.close()


def test_church_activity_participation_repository_rejects_duplicate_identity(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "church_activity_participation_duplicate.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        _prepare_database(connection)

        repository = ChurchActivityParticipationRepository(connection)

        participation = ChurchActivityParticipation(
            tenant_id="tenant-1",
            church_activity_id=1,
            membership_id=1,
        )

        repository.create(participation)

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(participation)

    finally:
        connection.close()
