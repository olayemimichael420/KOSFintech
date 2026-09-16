from services.tenant_identity_generator import TenantIdentityGenerator


def test_generates_non_empty_tenant_id():
    generator = TenantIdentityGenerator()

    tenant_id = generator.generate()

    assert isinstance(tenant_id, str)
    assert tenant_id


def test_generates_unique_tenant_ids():
    generator = TenantIdentityGenerator()

    first = generator.generate()
    second = generator.generate()

    assert first != second


def test_generated_tenant_id_is_opaque_uuid():
    generator = TenantIdentityGenerator()

    tenant_id = generator.generate()

    assert len(tenant_id) == 36
    assert tenant_id.count("-") == 4
