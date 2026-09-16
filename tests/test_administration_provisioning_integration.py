import database

from models.tenant import Tenant
from repositories.administration_repository import AdministrationRepository
from repositories.tenant_repository import TenantRepository
from services.administration_provisioning_service import (
    AdministrationProvisioningService,
)


def test_administration_provisioning_persists_administration(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "administration_provisioning.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        tenant_repository = TenantRepository(connection)
        tenant_repository.create(
            Tenant(
                id=None,
                tenant_id="tenant-001",
            )
        )

        repository = AdministrationRepository(connection)
        service = AdministrationProvisioningService(
            repository,
            tenant_repository,
        )

        created = service.create(
            tenant_id="tenant-001",
            name="Example Church",
            administration_type="church",
        )

        assert created.id is not None
        assert created.tenant_id == "tenant-001"
        assert created.name == "Example Church"
        assert created.administration_type == "church"
        assert created.status == "active"

        fetched = repository.get_by_id(created.id)

        assert fetched == created
    finally:
        connection.close()
