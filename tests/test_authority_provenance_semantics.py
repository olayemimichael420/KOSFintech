from authority_provenance_semantics import (
    AuthorityProvenanceRecord,
    AuthorityProvenanceValidator,
    ProvenanceResult,
)

MICHAEL_ID = "PERSON-MICHAEL-KEHINDE-OLAYEMI"


def record(**overrides):
    values = {
        "provenance_id": "PROV-MICHAEL-FOUNDING-001",
        "authority_id": "FOUNDING-AUTH-MICHAEL-001",
        "source_reference": "FOUNDING-SOURCE-001",
        "establishing_instrument": "FOUNDING-INSTRUMENT-001",
        "issuer_reference": "FOUNDING-ISSUER-001",
        "holder_reference": MICHAEL_ID,
        "jurisdiction": "KOS-FOUNDATIONAL-JURISDICTION",
        "scope": frozenset({"KOS", "KOSCORP", "KOSFINTECH"}),
        "powers": frozenset({
            "ESTABLISH_LEADERSHIP",
            "ESTABLISH_OFFICE",
            "ESTABLISH_OPERATIONAL_CAPACITY",
        }),
        "limits": frozenset({
            "SUBJECT_TO_CONSTITUTIONAL_ORDER",
            "SUBJECT_TO_SUCCESSION",
        }),
        "status": "ACTIVE",
        "effective_basis": "EFFECTIVE-BASIS-001",
        "evidence_class": "FOUNDING_INSTRUMENT",
    }
    values.update(overrides)
    return AuthorityProvenanceRecord(**values)


def test_complete_independent_founding_provenance_is_valid():
    result = AuthorityProvenanceValidator().validate(record())
    assert result.result is ProvenanceResult.VALID


def test_super_admin_role_is_not_authority_provenance():
    result = AuthorityProvenanceValidator().validate(
        record(
            establishing_instrument="SUPER_ADMIN-ROLE",
            evidence_class="TECHNICAL_RECORD",
        )
    )
    assert result.result is ProvenanceResult.INVALID


def test_visioner_classification_is_not_authority_provenance():
    result = AuthorityProvenanceValidator().validate(
        record(
            establishing_instrument="VISIONEER-CLASSIFICATION",
            evidence_class="TECHNICAL_RECORD",
        )
    )
    assert result.result is ProvenanceResult.INVALID


def test_historical_practice_is_not_authority_provenance():
    result = AuthorityProvenanceValidator().validate(
        record(
            establishing_instrument="HISTORICAL-PRACTICE",
            evidence_class="HISTORICAL_RECORD",
        )
    )
    assert result.result is ProvenanceResult.INVALID


def test_missing_establishing_instrument_is_rejected():
    result = AuthorityProvenanceValidator().validate(
        record(establishing_instrument="")
    )
    assert result.result is ProvenanceResult.INVALID


def test_missing_scope_is_rejected():
    result = AuthorityProvenanceValidator().validate(
        record(scope=frozenset())
    )
    assert result.result is ProvenanceResult.INVALID


def test_missing_limits_are_rejected():
    result = AuthorityProvenanceValidator().validate(
        record(limits=frozenset())
    )
    assert result.result is ProvenanceResult.INVALID


def test_proposed_status_is_not_sufficient_for_active_authority():
    result = AuthorityProvenanceValidator().validate(
        record(status="PROPOSED")
    )
    assert result.result is ProvenanceResult.INVALID
