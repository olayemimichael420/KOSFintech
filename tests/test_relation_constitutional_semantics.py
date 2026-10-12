from relation_constitutional_semantics import (
    AuthorityBasis,
    OfficeTarget,
    RelationConstitutionalSemanticValidator,
    SemanticResult,
)


def authority(**overrides):
    values = {
        "authority_id": "AUTH-FOUNDING",
        "status": "ACTIVE",
        "powers": frozenset({"ESTABLISH_OFFICE"}),
        "jurisdiction_id": "JUR-KOS",
        "scope": frozenset({"OFFICE-OPS"}),
        "provenance": "FOUNDING-BASIS-001",
    }
    values.update(overrides)
    return AuthorityBasis(**values)


def office(**overrides):
    values = {
        "office_id": "OFFICE-OPS",
        "jurisdiction_id": "JUR-KOS",
        "status": "ACTIVE",
    }
    values.update(overrides)
    return OfficeTarget(**values)


def test_r3_establishment_without_power_is_invalid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(powers=frozenset()), office()
    )
    assert result.result is SemanticResult.INVALID


def test_r3_establishment_with_valid_basis_is_valid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(), office()
    )
    assert result.result is SemanticResult.VALID


def test_r3_establishment_cross_jurisdiction_is_invalid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(), office(jurisdiction_id="JUR-OTHER")
    )
    assert result.result is SemanticResult.INVALID


def test_r3_establishment_out_of_scope_office_is_invalid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(scope=frozenset({"OFFICE-OTHER"})), office()
    )
    assert result.result is SemanticResult.INVALID


def test_r3_establishment_missing_provenance_is_invalid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(provenance=""), office()
    )
    assert result.result is SemanticResult.INVALID


def test_r3_establishment_proposed_authority_is_invalid():
    result = RelationConstitutionalSemanticValidator().validate_constitutes_office(
        authority(status="PROPOSED"), office()
    )
    assert result.result is SemanticResult.INVALID
