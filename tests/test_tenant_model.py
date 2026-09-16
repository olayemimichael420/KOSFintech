from models.tenant import Tenant


def test_tenant_model_defaults_to_active():
    tenant = Tenant(
        id=None,
        tenant_id="tenant-001",
    )

    assert tenant.id is None
    assert tenant.tenant_id == "tenant-001"
    assert tenant.status == "active"


def test_tenant_model_accepts_inactive_status():
    tenant = Tenant(
        id=1,
        tenant_id="tenant-001",
        status="inactive",
    )

    assert tenant.id == 1
    assert tenant.tenant_id == "tenant-001"
    assert tenant.status == "inactive"


def test_tenant_model_is_immutable():
    tenant = Tenant(
        id=None,
        tenant_id="tenant-001",
    )

    try:
        tenant.tenant_id = "tenant-002"
    except Exception:
        pass
    else:
        raise AssertionError("Tenant must be immutable")
