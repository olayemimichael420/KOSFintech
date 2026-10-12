from visioneer_semantics import (
    FoundingAuthorityReference,
    SemanticResult,
    VisioneerSemanticValidator,
    VisioneerSubject,
)
from technical_authority_firewall import (
    ConstitutionalAuthorityReference,
    TechnicalAuthorityFirewall,
    TechnicalCapability,
    FirewallResult,
)
from evidence_authority_firewall import (
    AuthorityReference,
    EvidenceAuthorityFirewall,
    EvidenceRecord,
    FirewallResult as EvidenceFirewallResult,
)

MICHAEL_ID = "PERSON-MICHAEL-KEHINDE-OLAYEMI"
SUPER_ADMIN = "SUPER_ADMIN"

def michael():
    return VisioneerSubject(
        subject_id=MICHAEL_ID,
        entity_type="SUBJECT",
        classification="VISIONEER",
    )

def founding_authority(**overrides):
    values = {
        "authority_id": "FOUNDING-AUTH-MICHAEL-001",
        "holder_id": MICHAEL_ID,
        "status": "ACTIVE",
        "powers": frozenset({
            "ESTABLISH_LEADERSHIP",
            "ESTABLISH_OFFICE",
            "ESTABLISH_OPERATIONAL_CAPACITY",
        }),
        "provenance": "INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
    }
    values.update(overrides)
    return FoundingAuthorityReference(**values)

def technical_capability():
    return TechnicalCapability(
        actor_id=MICHAEL_ID,
        capability=SUPER_ADMIN,
    )

def constitutional_authority():
    return ConstitutionalAuthorityReference(
        authority_id="FOUNDING-AUTH-MICHAEL-001",
        holder_id=MICHAEL_ID,
        status="ACTIVE",
        provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
    )

def evidence():
    return EvidenceRecord(
        evidence_id="EVIDENCE-MICHAEL-SUPER-ADMIN-001",
        evidence_class="TECHNICAL_RECORD",
        subject_id=MICHAEL_ID,
        claim="Michael Kehinde Olayemi is represented as the technical SUPER_ADMIN.",
        provenance="TECHNICAL-RECORD-001",
        authority_effect="NONE",
    )

def test_michael_can_be_represented_as_visioneer_subject():
    result = VisioneerSemanticValidator().validate_subject(michael())
    assert result.result is SemanticResult.VALID

def test_super_admin_alone_does_not_create_michaels_constitutional_authority():
    result = TechnicalAuthorityFirewall().validate_claim(
        technical_capability(),
        None,
    )
    assert result.result is FirewallResult.INVALID

def test_michael_visioneer_plus_super_admin_is_not_by_itself_authority():
    subject_result = VisioneerSemanticValidator().validate_subject(michael())
    technical_result = TechnicalAuthorityFirewall().validate_claim(
        technical_capability(),
        None,
    )
    assert subject_result.result is SemanticResult.VALID
    assert technical_result.result is FirewallResult.INVALID

def test_proposed_michael_founding_authority_is_not_active_authority():
    result = VisioneerSemanticValidator().validate_authority_holder(
        michael(),
        founding_authority(status="PROPOSED"),
    )
    assert result.result is SemanticResult.INVALID

def test_active_michael_founding_authority_can_be_separately_represented():
    result = VisioneerSemanticValidator().validate_authority_holder(
        michael(),
        founding_authority(),
    )
    assert result.result is SemanticResult.VALID

def test_michael_active_authority_and_super_admin_can_coexist():
    technical_result = TechnicalAuthorityFirewall().validate_claim(
        technical_capability(),
        constitutional_authority(),
    )
    visioneer_result = VisioneerSemanticValidator().validate_authority_holder(
        michael(),
        founding_authority(),
    )
    assert technical_result.result is FirewallResult.VALID
    assert visioneer_result.result is SemanticResult.VALID

def test_evidence_of_michaels_super_admin_status_does_not_create_authority():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(),
        None,
    )
    assert result.result is EvidenceFirewallResult.INVALID

def test_evidence_and_independent_michael_authority_can_coexist():
    result = EvidenceAuthorityFirewall().validate_claim(
        evidence(),
        AuthorityReference(
            authority_id="FOUNDING-AUTH-MICHAEL-001",
            holder_id=MICHAEL_ID,
            status="ACTIVE",
            provenance="INDEPENDENT-FOUNDING-AUTHORITY-BASIS",
        ),
    )
    assert result.result is not None
    assert result.result.value == "VALID"
