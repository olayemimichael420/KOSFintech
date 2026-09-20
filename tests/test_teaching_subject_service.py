import pytest

from models.teaching_subject import TeachingSubject
from repositories.teaching_subject_repository import TeachingSubjectRepository
from services.teaching_subject_service import TeachingSubjectService


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def test_create_and_get_are_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)
    service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    created = service.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    assert created.id is not None
    assert service.get(created.id) == created


def test_create_rejects_tenant_mismatch(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)
    service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    with pytest.raises(ValueError, match="teaching subject tenant mismatch"):
        service.create(
            TeachingSubject(
                id=None,
                tenant_id="tenant-other",
                name="Faith",
            )
        )


def test_list_is_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    _create_tenant(connection, "tenant-other")

    repository = TeachingSubjectRepository(connection)

    service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    service.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-cmos",
            name="Faith",
        )
    )

    other_service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-other",
    )

    other_service.create(
        TeachingSubject(
            id=None,
            tenant_id="tenant-other",
            name="Grace",
        )
    )

    assert [subject.name for subject in service.list()] == ["Faith"]
    assert [subject.name for subject in other_service.list()] == ["Grace"]


def test_create_requires_write_permission(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)

    service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=connection,
        user_id=999999,
    )

    with pytest.raises(PermissionError, match="teaching_subject.write"):
        service.create(
            TeachingSubject(
                id=None,
                tenant_id="tenant-cmos",
                name="Faith",
            )
        )


def test_list_and_get_require_read_permission(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")

    repository = TeachingSubjectRepository(connection)

    service = TeachingSubjectService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=connection,
        user_id=999999,
    )

    with pytest.raises(PermissionError, match="teaching_subject.read"):
        service.list()

    with pytest.raises(PermissionError, match="teaching_subject.read"):
        service.get(1)
