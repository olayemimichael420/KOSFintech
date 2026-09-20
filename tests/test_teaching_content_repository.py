import sqlite3

import database
import pytest

from models.teaching_content import TeachingContent
from repositories.teaching_content_repository import TeachingContentRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "teaching_content_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-a",),
    )
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-b",),
    )

    connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id, name, start_date, end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-a", "Session A", "2026-01-01", "2026-12-31"),
    )

    session_id = connection.execute(
        """
        SELECT id
        FROM teaching_sessions
        WHERE tenant_id = ? AND name = ?
        """,
        ("tenant-a", "Session A"),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_series (
            tenant_id,
            teaching_session_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            session_id,
            "Series A",
            "2026-02-01",
            "2026-10-31",
        ),
    )

    series_id = connection.execute(
        """
        SELECT id
        FROM teaching_series
        WHERE tenant_id = ? AND name = ?
        """,
        ("tenant-a", "Series A"),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_focuses (
            tenant_id,
            teaching_series_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-a",
            series_id,
            "Focus A",
            "2026-03-01",
            "2026-09-30",
        ),
    )

    connection.commit()

    return connection


def _focus_id(connection):
    return connection.execute(
        """
        SELECT id
        FROM teaching_focuses
        WHERE tenant_id = ? AND name = ?
        """,
        ("tenant-a", "Focus A"),
    ).fetchone()[0]


def test_create_and_get(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = TeachingContentRepository(connection)
    focus_id = _focus_id(connection)

    created = repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Introduction",
            description="Opening content",
            sequence=1,
        )
    )

    assert created.id is not None
    assert created.sequence == 1

    loaded = repository.get("tenant-a", created.id)

    assert loaded is not None
    assert loaded.name == "Introduction"
    assert loaded.description == "Opening content"
    assert loaded.sequence == 1
    assert loaded.tenant_id == "tenant-a"

    connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = TeachingContentRepository(connection)
    focus_id = _focus_id(connection)

    created = repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Tenant A Content",
        )
    )

    assert repository.get("tenant-a", created.id) is not None
    assert repository.get("tenant-b", created.id) is None

    connection.close()


def test_list_is_ordered_by_sequence(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = TeachingContentRepository(connection)
    focus_id = _focus_id(connection)

    repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Third",
            sequence=3,
        )
    )
    repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="First",
            sequence=1,
        )
    )
    repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Unordered",
        )
    )
    repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Second",
            sequence=2,
        )
    )

    contents = repository.list("tenant-a", focus_id)

    assert [content.name for content in contents] == [
        "First",
        "Second",
        "Third",
        "Unordered",
    ]

    connection.close()


def test_list_is_tenant_and_focus_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = TeachingContentRepository(connection)
    focus_id = _focus_id(connection)

    repository.create(
        TeachingContent(
            id=None,
            tenant_id="tenant-a",
            teaching_focus_id=focus_id,
            name="Focus Content",
        )
    )

    assert len(repository.list("tenant-a", focus_id)) == 1
    assert repository.list("tenant-b", focus_id) == []

    connection.close()


def test_missing_content_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = TeachingContentRepository(connection)

    assert repository.get("tenant-a", 999999) is None

    connection.close()
