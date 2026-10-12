from constitutional_semantic_pipeline import ConstitutionalSemanticPipeline, PipelineResult
from identity_holder_semantics import IdentityRecord
from relation_constitutional_semantics import AuthorityBasis, OfficeTarget


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


def subject():
    return IdentityRecord("PERSON-001", "SUBJECT", "PERSON")


def auth_identity():
    return IdentityRecord("AUTH-001", "AUTHORITY", "DELEGATED_AUTHORITY")


def office_identity():
    return IdentityRecord("OFFICE-001", "OFFICE", "INSTITUTIONAL_OFFICE")


def test_pipeline_valid_founding_establishment():
    result = ConstitutionalSemanticPipeline().check_constitutes_office(authority(), office())
    assert result.result is PipelineResult.VALID
    assert result.failed_layer is None


def test_pipeline_rejects_wrong_establishment_power():
    result = ConstitutionalSemanticPipeline().check_constitutes_office(
        authority(powers=frozenset()), office()
    )
    assert result.result is PipelineResult.INVALID
    assert result.failed_layer == "R3"


def test_pipeline_rejects_cross_jurisdiction_establishment():
    result = ConstitutionalSemanticPipeline().check_constitutes_office(
        authority(), office(jurisdiction_id="JUR-OTHER")
    )
    assert result.result is PipelineResult.INVALID
    assert result.failed_layer == "R3"


def test_pipeline_rejects_wrong_relation_direction():
    result = ConstitutionalSemanticPipeline().check_relation(
        "OCCUPIES", "OFFICE", "SUBJECT"
    )
    assert result.result is PipelineResult.INVALID
    assert result.failed_layer == "R2"


def test_pipeline_accepts_subject_holding_authority_semantically():
    result = ConstitutionalSemanticPipeline().check_subject_holds_authority(
        subject(), auth_identity()
    )
    assert result.result is PipelineResult.VALID


def test_pipeline_accepts_subject_occupying_office_semantically():
    result = ConstitutionalSemanticPipeline().check_subject_occupies_office(
        subject(), office_identity()
    )
    assert result.result is PipelineResult.VALID


def test_pipeline_rejects_office_as_holder_identity():
    result = ConstitutionalSemanticPipeline().check_subject_holds_authority(
        office_identity(), auth_identity()
    )
    assert result.result is PipelineResult.INVALID
    assert result.failed_layer == "R4"


def test_pipeline_unknown_relation_is_indeterminate():
    result = ConstitutionalSemanticPipeline().check_relation(
        "UNKNOWN", "SUBJECT", "ACTION"
    )
    assert result.result is PipelineResult.INDETERMINATE
    assert result.failed_layer == "R2"
