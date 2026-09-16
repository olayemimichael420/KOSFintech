import pytest
import database

from models.institution_anchor import InstitutionAnchor
from repositories.institution_anchor_repository import InstitutionAnchorRepository
from repositories.service_binding_repository import ServiceBindingRepository
from repositories.tenant_repository import TenantRepository
from models.tenant import Tenant
from services.service_binding_service import ServiceBindingService


def test_service_binding_service_create_and_get(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_service.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        binding_repository = ServiceBindingRepository(connection)
        tenant_repository = TenantRepository(connection)
        service = ServiceBindingService(
            binding_repository,
            tenant_repository,
            institution_repository,
        )

        tenant_repository.create(
            Tenant(id=None, tenant_id="tenant-001")
        )

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Example Church",
                provenance_reference="official-reference",
            )
        )

        created = service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-001",
        )

        assert created.id is not None
        assert created.institution_anchor_id == anchor.id
        assert created.tenant_id == "tenant-001"
        assert created.status == "active"

        fetched = service.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.institution_anchor_id == anchor.id
        assert fetched.tenant_id == "tenant-001"

    finally:
        connection.close()


def test_service_binding_service_list_active(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_service_list.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        binding_repository = ServiceBindingRepository(connection)
        tenant_repository = TenantRepository(connection)
        service = ServiceBindingService(
            binding_repository,
            tenant_repository,
            institution_repository,
        )

        tenant_repository.create(
            Tenant(id=None, tenant_id="tenant-active")
        )
        tenant_repository.create(
            Tenant(id=None, tenant_id="tenant-inactive")
        )

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="school",
                name="Example School",
                provenance_reference="official-reference",
            )
        )

        service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-active",
        )

        service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-inactive",
            status="inactive",
        )

        active = service.list_active()

        assert len(active) == 1
        assert active[0].tenant_id == "tenant-active"
        assert active[0].status == "active"

    finally:
        connection.close()


class StubServiceBindingRepository:
    def __init__(self):
        self.created = []

    def create(self, binding):
        self.created.append(binding)
        return binding


class StubTenantRepository:
    def get_by_tenant_id(self, tenant_id):
        return None

class StubInstitutionAnchorRepository:
    def get(self, anchor_id):
        return None



def test_service_binding_service_rejects_unknown_tenant():
    binding_repository = StubServiceBindingRepository()
    tenant_repository = StubTenantRepository()

    service = ServiceBindingService(
        binding_repository,
        tenant_repository,
        StubInstitutionAnchorRepository(),
    )

    with pytest.raises(ValueError, match="tenant not found"):
        service.create(
            institution_anchor_id=1,
            tenant_id="tenant-unknown",
        )

def test_service_binding_service_rejects_unknown_institution_anchor():
    binding_repository = StubServiceBindingRepository()

    class ExistingTenantRepository:
        def get_by_tenant_id(self, tenant_id):
            return Tenant(id=1, tenant_id=tenant_id)

    class StubInstitutionAnchorRepository:
        def get(self, anchor_id):
            return None

    service = ServiceBindingService(
        binding_repository,
        ExistingTenantRepository(),
        StubInstitutionAnchorRepository(),
    )

    with pytest.raises(
        ValueError,
        match="institution anchor not found",
    ):
        service.create(
            institution_anchor_id=999,
            tenant_id="tenant-001",
        )
