import sqlite3

import database
from models.person import Person
from models.person_user import PersonUserLink
from models.user import User
from repositories.person_repository import PersonRepository
from repositories.person_user_repository import PersonUserRepository
from repositories.user_repository import UserRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "person_user_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        ("tenant-a",),
    )
    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        ("tenant-b",),
    )
    connection.commit()

    return connection


def _create_person(connection, name):
    return PersonRepository(connection).create(
        Person(id=None, name=name)
    )


def _create_user(connection, tenant_id, name):
    return UserRepository(connection).create(
        User(
            id=None,
            tenant_id=tenant_id,
            name=name,
            email=None,
            role="member",
        )
    )


def test_create_and_get_by_user(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)

    person = _create_person(connection, "Michael Olayemi")
    user = _create_user(connection, "tenant-a", "Michael")

    repository = PersonUserRepository(connection)

    link = repository.create(
        PersonUserLink(
            person_id=person.id,
            tenant_id="tenant-a",
            user_id=user.id,
        )
    )

    assert repository.get_by_user("tenant-a", user.id) == link

    connection.close()


def test_person_can_have_users_in_multiple_tenants(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)

    person = _create_person(connection, "Michael Olayemi")
    user_a = _create_user(connection, "tenant-a", "Michael A")
    user_b = _create_user(connection, "tenant-b", "Michael B")

    repository = PersonUserRepository(connection)

    repository.create(
        PersonUserLink(
            person_id=person.id,
            tenant_id="tenant-a",
            user_id=user_a.id,
        )
    )
    repository.create(
        PersonUserLink(
            person_id=person.id,
            tenant_id="tenant-b",
            user_id=user_b.id,
        )
    )

    links = repository.list_by_person(person.id)

    assert [(link.tenant_id, link.user_id) for link in links] == [
        ("tenant-a", user_a.id),
        ("tenant-b", user_b.id),
    ]

    connection.close()


def test_user_can_have_only_one_person(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)

    person_a = _create_person(connection, "Person A")
    person_b = _create_person(connection, "Person B")
    user = _create_user(connection, "tenant-a", "User")

    repository = PersonUserRepository(connection)

    repository.create(
        PersonUserLink(
            person_id=person_a.id,
            tenant_id="tenant-a",
            user_id=user.id,
        )
    )

    try:
        repository.create(
            PersonUserLink(
                person_id=person_b.id,
                tenant_id="tenant-a",
                user_id=user.id,
            )
        )
        assert False, "one user must not represent multiple persons"
    except Exception as exc:
        assert "UNIQUE" in str(exc).upper()

    connection.close()


def test_cross_tenant_user_reference_is_rejected(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)

    person = _create_person(connection, "Person")
    user = _create_user(connection, "tenant-a", "User")

    repository = PersonUserRepository(connection)

    try:
        repository.create(
            PersonUserLink(
                person_id=person.id,
                tenant_id="tenant-b",
                user_id=user.id,
            )
        )
        assert False, "cross-tenant user association must be rejected"
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper()

    connection.close()


def test_missing_person_reference_is_rejected(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)

    user = _create_user(connection, "tenant-a", "User")

    repository = PersonUserRepository(connection)

    try:
        repository.create(
            PersonUserLink(
                person_id=999999,
                tenant_id="tenant-a",
                user_id=user.id,
            )
        )
        assert False, "missing person reference must be rejected"
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper()

    connection.close()
