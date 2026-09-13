import sqlite3
import uuid

import pytest

from database import get_connection, init_db
from models.academic_class import AcademicClass
from repositories.academic_class_repository import AcademicClassRepository
from services.academic_class_service import AcademicClassService


def setup_connection():
    init_db()
    connection = get_connection()

    tenant_id = f"academic-class-service-school-{uuid.uuid4().hex}"

    connection.execute(
        """
        INSERT OR IGNORE INTO schools (
            tenant_id,
            name,
            school_type,
            country,
            currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            "Academic Class Service School",
            "secondary",
            "NG",
            "NGN",
        ),
    )
    connection.commit()

    return connection, tenant_id


def test_create_enforces_tenant_scope():
    connection, tenant_id = setup_connection()

    repository = AcademicClassRepository(connection)
    service = AcademicClassService(
        repository,
        tenant_id,
        connection=connection,
    )

    academic_class = AcademicClass(
        id=None,
        tenant_id=tenant_id,
        name="JSS 1",
        education_level="secondary",
        sequence=1,
    )

    created = service.create(academic_class)

    assert created.id is not None
    assert created.name == "JSS 1"

    connection.close()


def test_create_rejects_tenant_mismatch():
    connection, tenant_id = setup_connection()

    repository = AcademicClassRepository(connection)
    service = AcademicClassService(
        repository,
        tenant_id,
        connection=connection,
    )

    academic_class = AcademicClass(
        id=None,
        tenant_id="different-school",
        name="Year 7",
    )

    with pytest.raises(ValueError, match="academic class tenant mismatch"):
        service.create(academic_class)

    connection.close()


def test_list_is_tenant_scoped():
    connection, tenant_id = setup_connection()

    repository = AcademicClassRepository(connection)
    service = AcademicClassService(
        repository,
        tenant_id,
        connection=connection,
    )

    service.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_id,
            name="Primary 5",
        )
    )

    classes = service.list()

    assert len(classes) == 1
    assert classes[0].tenant_id == tenant_id
    assert classes[0].name == "Primary 5"

    connection.close()


def test_get_is_tenant_scoped():
    connection, tenant_id = setup_connection()

    repository = AcademicClassRepository(connection)
    service = AcademicClassService(
        repository,
        tenant_id,
        connection=connection,
    )

    created = service.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_id,
            name="Level 100",
        )
    )

    found = service.get(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.tenant_id == tenant_id

    connection.close()


def test_permission_constants_are_defined():
    assert AcademicClassService.READ_PERMISSION == "academic_class.read"
    assert AcademicClassService.WRITE_PERMISSION == "academic_class.write"
