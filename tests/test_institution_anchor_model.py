from models.institution_anchor import InstitutionAnchor


def test_institution_anchor_defaults():
    anchor = InstitutionAnchor(
        id=None,
        institution_type="church",
        name="Example Church",
        provenance_reference="https://example.org/church",
    )

    assert anchor.id is None
    assert anchor.institution_type == "church"
    assert anchor.name == "Example Church"
    assert anchor.provenance_reference == "https://example.org/church"
    assert anchor.verification_status == "pending"
    assert anchor.status == "active"
    assert anchor.created_at is None


def test_institution_anchor_supports_multiple_institution_types():
    church = InstitutionAnchor(
        id=1,
        institution_type="church",
        name="Example Church",
        provenance_reference="church-reference",
    )

    school = InstitutionAnchor(
        id=2,
        institution_type="school",
        name="Example School",
        provenance_reference="school-reference",
    )

    hospital = InstitutionAnchor(
        id=3,
        institution_type="hospital",
        name="Example Hospital",
        provenance_reference="hospital-reference",
    )

    assert church.institution_type == "church"
    assert school.institution_type == "school"
    assert hospital.institution_type == "hospital"


def test_institution_anchor_verification_and_status_are_independent():
    anchor = InstitutionAnchor(
        id=1,
        institution_type="church",
        name="Example Church",
        provenance_reference="official-reference",
        verification_status="verified",
        status="inactive",
    )

    assert anchor.verification_status == "verified"
    assert anchor.status == "inactive"
    assert anchor.provenance_reference == "official-reference"
