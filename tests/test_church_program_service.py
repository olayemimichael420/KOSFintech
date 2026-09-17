import uuid

import pytest

from database import get_connection, init_db
from models.church_program import ChurchProgram
from repositories.church_program_repository import ChurchProgramRepository
from services.church_program_service import ChurchProgramService


def _tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


@pytest.fixture
def service():
    init_db()
    connection = get_connection()
    tenant_id = f"church-program-service-{uuid.uuid4().hex}"

    try:
        _tenant(connection, tenant_id)
        repository = ChurchProgramRepository(connection)
        yield (
            ChurchProgramService(
                repository=repository,
                tenant_id=tenant_id,
                connection=None,
                user_id=None,
            ),
            tenant_id,
        )
    finally:
        connection.close()


def test_create_and_get_program(service):
    program_service, tenant_id = service

    created = program_service.create(
        ChurchProgram(
            id=None,
            tenant_id=tenant_id,
            name="Discipleship",
        )
    )

    loaded = program_service.get(created.id)

    assert loaded is not None
    assert loaded.name == "Discipleship"


def test_create_rejects_tenant_mismatch(service):
    program_service, tenant_id = service

    with pytest.raises(ValueError, match="tenant mismatch"):
        program_service.create(
            ChurchProgram(
                id=None,
                tenant_id=f"other-{uuid.uuid4().hex}",
                name="Bible Study",
            )
        )


def test_list_is_tenant_scoped(service):
    program_service, tenant_id = service

    program_service.create(
        ChurchProgram(
            id=None,
            tenant_id=tenant_id,
            name="Prayer",
        )
    )

    programs = program_service.list()

    assert len(programs) == 1
    assert programs[0].tenant_id == tenant_id
