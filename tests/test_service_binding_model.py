from models.service_binding import ServiceBinding


def test_service_binding_defaults():
    binding = ServiceBinding(
        id=None,
        institution_anchor_id=1,
        tenant_id="tenant-001",
    )

    assert binding.id is None
    assert binding.institution_anchor_id == 1
    assert binding.tenant_id == "tenant-001"
    assert binding.status == "active"


def test_service_binding_can_be_inactive():
    binding = ServiceBinding(
        id=7,
        institution_anchor_id=2,
        tenant_id="tenant-002",
        status="inactive",
    )

    assert binding.id == 7
    assert binding.institution_anchor_id == 2
    assert binding.tenant_id == "tenant-002"
    assert binding.status == "inactive"
