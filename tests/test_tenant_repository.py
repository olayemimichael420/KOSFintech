from models.tenant import Tenant
from repositories.tenant_repository import TenantRepository


def test_create_tenant_persists_and_returns_tenant(db_connection):
    repository = TenantRepository(db_connection)

    tenant = repository.create(
        Tenant(
            id=None,
            tenant_id="tenant-001",
        )
    )

    assert tenant.id is not None
    assert tenant.tenant_id == "tenant-001"
    assert tenant.status == "active"


def test_get_tenant_is_scoped_by_tenant_id(db_connection):
    repository = TenantRepository(db_connection)

    created = repository.create(
        Tenant(
            id=None,
            tenant_id="tenant-001",
        )
    )

    assert repository.get("tenant-001", created.id) == created
    assert repository.get("tenant-002", created.id) is None


def test_list_active_tenants_returns_active_only(db_connection):
    repository = TenantRepository(db_connection)

    repository.create(
        Tenant(
            id=None,
            tenant_id="tenant-active",
            status="active",
        )
    )
    repository.create(
        Tenant(
            id=None,
            tenant_id="tenant-inactive",
            status="inactive",
        )
    )

    tenants = repository.list_active()

    assert [tenant.tenant_id for tenant in tenants] == [
        "tenant-active"
    ]


def test_get_tenant_by_tenant_id_returns_tenant(db_connection):
    repository = TenantRepository(db_connection)
    created = repository.create(
        Tenant(
            id=None,
            tenant_id="tenant-lookup",
        )
    )

    assert repository.get_by_tenant_id("tenant-lookup") == created


def test_get_tenant_by_tenant_id_returns_none_for_unknown_tenant(
    db_connection,
):
    repository = TenantRepository(db_connection)

    assert repository.get_by_tenant_id("does-not-exist") is None
