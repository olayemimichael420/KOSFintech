from models.church_anchor import ChurchAnchor


def test_church_anchor_defaults():
    anchor = ChurchAnchor(
        id=None,
        tenant_id="tenant-001",
        name="Example Church",
        provenance_reference="https://example.org/church",
    )

    assert anchor.id is None
    assert anchor.tenant_id == "tenant-001"
    assert anchor.name == "Example Church"
    assert anchor.provenance_reference == "https://example.org/church"
    assert anchor.verification_status == "pending"
    assert anchor.status == "active"
    assert anchor.created_at is None


def test_church_anchor_preserves_verified_state():
    anchor = ChurchAnchor(
        id=1,
        tenant_id="tenant-001",
        name="Verified Church",
        provenance_reference="official-reference",
        verification_status="verified",
        status="active",
    )

    assert anchor.verification_status == "verified"
    assert anchor.status == "active"


def test_church_anchor_can_be_inactive_without_changing_provenance():
    anchor = ChurchAnchor(
        id=1,
        tenant_id="tenant-001",
        name="Inactive Church",
        provenance_reference="official-reference",
        verification_status="verified",
        status="inactive",
    )

    assert anchor.verification_status == "verified"
    assert anchor.status == "inactive"
    assert anchor.provenance_reference == "official-reference"
