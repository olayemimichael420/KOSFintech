from repositories.tenant_repository import TenantRepository
from services.tenant_identity_generator import TenantIdentityGenerator
import pytest

from models.tenant import Tenant
from services.tenant_service import TenantService


class StubTenantRepository:
    def __init__(self):
        self.created = []

    def create(self, tenant):
        self.created.append(tenant)
        return Tenant(
            id=1,
            tenant_id=tenant.tenant_id,
            status=tenant.status,
        )


def test_create_tenant_validates_and_delegates():
    repository = StubTenantRepository()
    service = TenantService(repository)

    created = service.create("tenant-001")

    assert created == Tenant(
        id=1,
        tenant_id="tenant-001",
        status="active",
    )

    assert repository.created == [
        Tenant(
            id=None,
            tenant_id="tenant-001",
            status="active",
        )
    ]


def test_create_tenant_rejects_blank_tenant_id():
    repository = StubTenantRepository()
    service = TenantService(repository)

    with pytest.raises(ValueError, match="tenant_id is required"):
        service.create("   ")


def test_create_tenant_rejects_invalid_status():
    repository = StubTenantRepository()
    service = TenantService(repository)

    with pytest.raises(ValueError, match="invalid tenant status"):
        service.create("tenant-001", status="suspended")


def test_create_generates_tenant_id_when_not_supplied(db_connection):
    repository = TenantRepository(db_connection)
    generator = TenantIdentityGenerator()
    service = TenantService(
        repository=repository,
        identity_generator=generator,
    )

    tenant = service.create()

    assert tenant.tenant_id
    assert len(tenant.tenant_id) == 36
    assert tenant.tenant_id.count("-") == 4
