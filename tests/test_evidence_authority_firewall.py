from evidence_authority_firewall import (
    AuthorityReference,
    EvidenceAuthorityFirewall,
    EvidenceRecord,
    FirewallResult,
)


def evidence(**overrides):
    values = {
        "evidence_id": "E-001",
        "evidence_class": "TECHNICAL_RECORD",
        "subject_id": "ACTOR-001",
        "claim": "actor performed an administrative operation",
        "provenance": "SYSTEM-LOG-001",
        "authority_effect": "NONE",
    }
    values.update(overrides)
    return EvidenceRecord(**values)


def authority(**overrides):
    values = {
        "authority_id": "AUTH-001",
        "holder_id": "ACTOR-001",
        "status": "ACTIVE",
        "provenance": "INDEPENDENT-AUTHORITY-BASIS",
    }
    values.update(overrides)
    return AuthorityReference(**values)


def test_technical_record_cannot_create_authority():
    result = EvidenceAuthorityFirewall().validate_claim(evidence(), None)
    assert result.result is FirewallResult.INVALID


def test_historical_record_cannot_create_authority():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(evidence_class="HISTORICAL_RECORD"), None
    )
    assert result.result is FirewallResult.INVALID


def test_evidence_cannot_declare_authority_effect():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(authority_effect="ESTABLISHES_AUTHORITY"), authority()
    )
    assert result.result is FirewallResult.INVALID


def test_evidence_with_invalid_claim_or_provenance_is_rejected():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(claim="", provenance=""), authority()
    )
    assert result.result is FirewallResult.INVALID


def test_mismatched_authority_holder_is_rejected():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(), authority(holder_id="OTHER-ACTOR")
    )
    assert result.result is FirewallResult.INVALID


def test_proposed_authority_does_not_complete_evidence_claim():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(), authority(status="PROPOSED")
    )
    assert result.result is FirewallResult.INVALID


def test_evidence_and_independent_authority_may_coexist_without_equivalence():
    result = EvidenceAuthorityFirewall().validate_claim(evidence(), authority())
    assert result.result is FirewallResult.VALID
