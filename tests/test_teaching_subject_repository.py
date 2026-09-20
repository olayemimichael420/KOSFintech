import pytest

from models.teaching_subject import TeachingSubject
from repositories.teaching_subject_repository import TeachingSubjectRepository


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def test_create_persists_and_returns_subject(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)

    subject = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    assert subject.id is not None
    assert repository.get("tenant-cmos", subject.id) == subject


def test_get_is_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)

    subject = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    assert repository.get("tenant-cmos", subject.id) == subject
    assert repository.get("other-tenant", subject.id) is None


def test_list_is_tenant_scoped_and_ordered_by_name(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    _create_tenant(connection, "tenant-other")

    repository = TeachingSubjectRepository(connection)

    faith = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    hope = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Hope",
        )
    )

    repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-other",
            name="Grace",
        )
    )

    assert repository.list("tenant-cmos") == [faith, hope]


def test_duplicate_name_within_same_tenant_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)

    repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    with pytest.raises(Exception):
        repository.create(
            TeachingSubject(
                id=None,
                tenant_id="tenant-cmos",
                name="Faith",
            )
        )


def test_same_name_is_allowed_in_different_tenants(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    _create_tenant(connection, "tenant-other")

    repository = TeachingSubjectRepository(connection)

    first = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    second = repository.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-other",
            name="Faith",
        )
    )

    assert first.id != second.id
    assert repository.get("tenant-cmos", first.id) == first
    assert repository.get("tenant-other", second.id) == second
