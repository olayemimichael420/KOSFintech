import uuid

import pytest

from database import get_connection, init_db
from models.academic_subject import AcademicSubject
from repositories.academic_subject_repository import AcademicSubjectRepository
from services.academic_subject_service import AcademicSubjectService


def _school(connection, tenant_id):
    connection.execute(
        """
        INSERT INTO schools (
            tenant_id, name, school_type, country, currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_id, "Test School", "secondary", "NG", "NGN"),
    )
    connection.commit()


@pytest.fixture
def service():
    init_db()
    connection = get_connection()
    tenant_id = f"subject-service-{uuid.uuid4().hex}"

    try:
        _school(connection, tenant_id)
        repository = AcademicSubjectRepository(connection)
        yield (
            AcademicSubjectService(
                repository=repository,
                tenant_id=tenant_id,
                connection=None,
                user_id=None,
            ),
            tenant_id,
        )
    finally:
        connection.close()


def test_create_and_get_subject(service):
    subject_service, tenant_id = service

    created = subject_service.create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_id,
            name="Mathematics",
        )
    )

    loaded = subject_service.get(created.id)

    assert loaded is not None
    assert loaded.name == "Mathematics"


def test_create_rejects_tenant_mismatch(service):
    subject_service, tenant_id = service

    with pytest.raises(ValueError, match="tenant mismatch"):
        subject_service.create(
            AcademicSubject(
                id=None,
                tenant_id=f"other-{uuid.uuid4().hex}",
                name="Physics",
            )
        )


def test_list_is_tenant_scoped(service):
    subject_service, tenant_id = service

    subject_service.create(
        AcademicSubject(
            id=None,
            tenant_id=tenant_id,
            name="Chemistry",
        )
    )

    subjects = subject_service.list()

    assert len(subjects) == 1
    assert subjects[0].tenant_id == tenant_id
