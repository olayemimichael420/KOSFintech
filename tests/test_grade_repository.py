import sqlite3

import pytest

import database
from models.grade import Grade
from repositories.grade_repository import GradeRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "grade_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed(connection):
    connection.execute(
        "INSERT INTO tenants (tenant_id) VALUES (?)",
        ("tenant-cmos",),
    )
    connection.commit()


def test_create_and_get_grade(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = GradeRepository(connection)

        grade = Grade(
            id=None,
            tenant_id="tenant-cmos",
            name="A",
            description="Excellent",
            minimum_score=80,
            maximum_score=100,
        )

        created = repository.create(grade)
        fetched = repository.get("tenant-cmos", created.id)

        assert created.id is not None
        assert fetched == created
    finally:
        connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = GradeRepository(connection)

        created = repository.create(
            Grade(
                id=None,
                tenant_id="tenant-cmos",
                name="A",
                minimum_score=80,
                maximum_score=100,
            )
        )

        assert repository.get("other-tenant", created.id) is None
    finally:
        connection.close()


def test_list_by_tenant_is_tenant_scoped_and_ordered(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = GradeRepository(connection)

        first = repository.create(
            Grade(
                id=None,
                tenant_id="tenant-cmos",
                name="B",
                minimum_score=60,
                maximum_score=79,
            )
        )
        second = repository.create(
            Grade(
                id=None,
                tenant_id="tenant-cmos",
                name="A",
                minimum_score=80,
                maximum_score=100,
            )
        )

        results = repository.list_by_tenant("tenant-cmos")

        assert [item.id for item in results] == [
            first.id,
            second.id,
        ]
        assert repository.list_by_tenant("other-tenant") == []
    finally:
        connection.close()


def test_unknown_grade_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = GradeRepository(connection)

        assert repository.get("tenant-cmos", 999999) is None
    finally:
        connection.close()


def test_grade_name_is_unique_per_tenant(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = GradeRepository(connection)

        repository.create(
            Grade(
                id=None,
                tenant_id="tenant-cmos",
                name="A",
                minimum_score=80,
                maximum_score=100,
            )
        )

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(
                Grade(
                    id=None,
                    tenant_id="tenant-cmos",
                    name="A",
                    minimum_score=80,
                    maximum_score=100,
                )
            )
    finally:
        connection.close()
