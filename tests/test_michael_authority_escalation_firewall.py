from visioneer_semantics import (
    FoundingAuthorityReference,
    SemanticResult,
    VisioneerSemanticValidator,
    VisioneerSubject,
)
from technical_authority_firewall import (
    ConstitutionalAuthorityReference,
    FirewallResult as TechnicalFirewallResult,
    TechnicalAuthorityFirewall,
    TechnicalCapability,
)
from evidence_authority_firewall import (
    AuthorityReference,
    EvidenceAuthorityFirewall,
    EvidenceRecord,
    FirewallResult as EvidenceFirewallResult,
)

MICHAEL_ID = "PERSON-MICHAEL-KEHINDE-OLAYEMI"

def subject():
    return VisioneerSubject(
        subject_id=MICHAEL_ID,
        entity_type="SUBJECT",
        classification="VISIONEER",
    )

def capability():
    return TechnicalCapability(
        actor_id=MICHAEL_ID,
        capability="SUPER_ADMIN",
    )

def proposed_authority():
    return FoundingAuthorityReference(
        authority_id="FOUNDING-AUTH-MICHAEL-001",
        holder_id=MICHAEL_ID,
        status="PROPOSED",
        powers=frozenset({
            "ESTABLISH_LEADERSHIP",
            "ESTABLISH_OFFICE",
            "ESTABLISH_OPERATIONAL_CAPACITY",
        }),
        provenance="PROPOSED-FOUNDING-BASIS",
    )

def active_authority():
    return FoundingAuthorityReference(
        authority_id="FOUNDING-AUTH-MICHAEL-001",
        holder_id=MICHAEL_ID,
        status="ACTIVE",
        powers=frozenset({
            "ESTABLISH_LEADERSHIP",
            "ESTABLISH_OFFICE",
            "ESTABLISH_OPERATIONAL_CAPACITY",
        }),
        provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
    )

def technical_authority(status="ACTIVE", provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS"):
    return ConstitutionalAuthorityReference(
        authority_id="FOUNDING-AUTH-MICHAEL-001",
        holder_id=MICHAEL_ID,
        status=status,
        provenance=provenance,
    )

def technical_evidence():
    return EvidenceRecord(
        evidence_id="E-TECH-MICHAEL-001",
        evidence_class="TECHNICAL_RECORD",
        subject_id=MICHAEL_ID,
        claim="Michael Kehinde Olayemi is represented as SUPER_ADMIN.",
        provenance="SYSTEM-ADMIN-RECORD-001",
        authority_effect="NONE",
    )

def historical_evidence():
    return EvidenceRecord(
        evidence_id="E-HIST-MICHAEL-001",
        evidence_class="HISTORICAL_RECORD",
        subject_id=MICHAEL_ID,
        claim="Historical practice records Michael as a founding actor.",
        provenance="HISTORICAL-RECORD-001",
        authority_effect="NONE",
    )

def test_visioner_super_admin_technical_and_historical_signals_do_not_create_authority():
    vision_result = VisioneerSemanticValidator().validate_subject(subject())
    technical_result = TechnicalAuthorityFirewall().validate_claim(capability(), None)
    technical_evidence_result = EvidenceAuthorityFirewall().validate_claim(technical_evidence(), None)
    historical_result = EvidenceAuthorityFirewall().validate_claim(historical_evidence(), None)

    assert vision_result.result is SemanticResult.VALID
    assert technical_result.result is TechnicalFirewallResult.INVALID
    assert technical_evidence_result.result is EvidenceFirewallResult.INVALID
    assert historical_result.result is EvidenceFirewallResult.INVALID

def test_proposed_authority_cannot_be_promoted_by_accumulated_signals():
    vision_result = VisioneerSemanticValidator().validate_authority_holder(
        subject(), proposed_authority()
    )
    technical_result = TechnicalAuthorityFirewall().validate_claim(
        capability(),
        technical_authority(status="PROPOSED", provenance="PROPOSED-FOUNDING-BASIS"),
    )
    evidence_result = EvidenceAuthorityFirewall().validate_claim(
        technical_evidence(),
        AuthorityReference(
            authority_id="FOUNDING-AUTH-MICHAEL-001",
            holder_id=MICHAEL_ID,
            status="PROPOSED",
            provenance="PROPOSED-FOUNDING-BASIS",
        ),
    )

    assert vision_result.result is SemanticResult.INVALID
    assert technical_result.result is TechnicalFirewallResult.INVALID
    assert evidence_result.result is EvidenceFirewallResult.INVALID

def test_historical_practice_cannot_become_authority_through_super_admin_status():
    result = EvidenceAuthorityFirewall().validate_claim(
        historical_evidence(),
        AuthorityReference(
            authority_id="FOUNDING-AUTH-MICHAEL-001",
            holder_id=MICHAEL_ID,
            status="PROPOSED",
            provenance="HISTORICAL-PRACTICE-ONLY",
        ),
    )
    assert result.result is EvidenceFirewallResult.INVALID

def test_independent_active_authority_allows_full_correspondence():
    vision_result = VisioneerSemanticValidator().validate_authority_holder(
        subject(), active_authority()
    )
    technical_result = TechnicalAuthorityFirewall().validate_claim(
        capability(), technical_authority()
    )
    technical_evidence_result = EvidenceAuthorityFirewall().validate_claim(
        technical_evidence(),
        AuthorityReference(
            authority_id="FOUNDING-AUTH-MICHAEL-001",
            holder_id=MICHAEL_ID,
            status="ACTIVE",
            provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
        ),
    )
    historical_evidence_result = EvidenceAuthorityFirewall().validate_claim(
        historical_evidence(),
        AuthorityReference(
            authority_id="FOUNDING-AUTH-MICHAEL-001",
            holder_id=MICHAEL_ID,
            status="ACTIVE",
            provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
        ),
    )

    assert vision_result.result is SemanticResult.VALID
    assert technical_result.result is TechnicalFirewallResult.VALID
    assert technical_evidence_result.result is EvidenceFirewallResult.VALID
    assert historical_evidence_result.result is EvidenceFirewallResult.VALID
