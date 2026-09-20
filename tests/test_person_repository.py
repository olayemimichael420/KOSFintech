import sqlite3

import database
from models.person import Person
from repositories.person_repository import PersonRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "person_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def test_create_and_get(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = PersonRepository(connection)

    created = repository.create(
        Person(
            id=None,
            name="Michael Olayemi",
        )
    )

    assert created.id is not None
    assert created.name == "Michael Olayemi"
    assert created.status == "active"

    loaded = repository.get(created.id)

    assert loaded == created

    connection.close()


def test_person_is_not_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = PersonRepository(connection)

    first = repository.create(
        Person(
            id=None,
            name="Person One",
        )
    )
    second = repository.create(
        Person(
            id=None,
            name="Person Two",
        )
    )

    assert first.id != second.id
    assert repository.get(first.id) == first
    assert repository.get(second.id) == second

    connection.close()


def test_list_returns_people(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = PersonRepository(connection)

    repository.create(Person(id=None, name="Person A"))
    repository.create(Person(id=None, name="Person B"))

    people = repository.list()

    assert [person.name for person in people] == [
        "Person A",
        "Person B",
    ]

    connection.close()


def test_missing_person_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = PersonRepository(connection)

    assert repository.get(999999) is None

    connection.close()
