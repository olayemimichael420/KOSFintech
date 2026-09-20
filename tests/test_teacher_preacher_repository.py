import sqlite3

import pytest

from models.person import Person
from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def test_create_and_get_teacher_preacher(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    person = PersonRepository(connection).create(
        Person(id=None, name="Teacher One")
    )
    repository = TeacherPreacherRepository(connection)

    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    result = repository.get("tenant-001", capacity.id)

    assert result == capacity


def test_list_is_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    people = PersonRepository(connection)
    person_one = people.create(Person(id=None, name="Teacher One"))
    person_two = people.create(Person(id=None, name="Teacher Two"))

    repository = TeacherPreacherRepository(connection)

    repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_one.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )
    repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-002",
            person_id=person_two.id,
            role=TeacherPreacherRole.PREACHER,
        )
    )

    result = repository.list("tenant-001")

    assert len(result) == 1
    assert result[0].person_id == person_one.id


def test_get_is_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    person = PersonRepository(connection).create(
        Person(id=None, name="Teacher One")
    )
    repository = TeacherPreacherRepository(connection)

    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER_PREACHER,
        )
    )

    assert repository.get("tenant-002", capacity.id) is None


def test_missing_person_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    repository = TeacherPreacherRepository(connection)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            TeacherPreacher(
                id=None,
                tenant_id="tenant-001",
                person_id=999999,
                role=TeacherPreacherRole.TEACHER,
            )
        )


def test_one_teacher_preacher_capacity_per_person_per_tenant(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    person = PersonRepository(connection).create(
        Person(id=None, name="Teacher One")
    )
    repository = TeacherPreacherRepository(connection)

    repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            TeacherPreacher(
                id=None,
                tenant_id="tenant-001",
                person_id=person.id,
                role=TeacherPreacherRole.PREACHER,
            )
        )


def test_same_person_can_have_capacity_in_another_tenant(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")

    person = PersonRepository(connection).create(
        Person(id=None, name="Teacher One")
    )
    repository = TeacherPreacherRepository(connection)

    first = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER,
        )
    )
    second = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-002",
            person_id=person.id,
            role=TeacherPreacherRole.PREACHER,
        )
    )

    assert first.tenant_id == "tenant-001"
    assert second.tenant_id == "tenant-002"


def test_role_and_status_round_trip(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")

    person = PersonRepository(connection).create(
        Person(id=None, name="Teacher One")
    )
    repository = TeacherPreacherRepository(connection)

    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person.id,
            role=TeacherPreacherRole.TEACHER_PREACHER,
            status="inactive",
        )
    )

    result = repository.get("tenant-001", capacity.id)

    assert result.role == TeacherPreacherRole.TEACHER_PREACHER
    assert result.status == "inactive"
