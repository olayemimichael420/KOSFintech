from dataclasses import dataclass
from enum import Enum


class FirewallResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_class: str
    subject_id: str
    claim: str
    provenance: str
    authority_effect: str = "NONE"


@dataclass(frozen=True)
class AuthorityReference:
    authority_id: str
    holder_id: str
    status: str
    provenance: str


@dataclass(frozen=True)
class EvidenceAuthorityCheck:
    result: FirewallResult
    rule: str
    reason: str


class EvidenceAuthorityFirewall:
    """Developmental firewall: evidence cannot promote itself into authority."""

    def validate_claim(self, evidence: EvidenceRecord, authority: AuthorityReference | None) -> EvidenceAuthorityCheck:
        if evidence.authority_effect != "NONE":
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-01",
                "evidence declares a non-NONE authority effect",
            )

        if not evidence.claim.strip() or not evidence.provenance.strip():
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-02",
                "evidence claim and provenance are required",
            )

        if authority is None:
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-03",
                "evidence has no independently represented authority basis",
            )

        if authority.holder_id != evidence.subject_id:
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-04",
                "independent authority holder does not match represented subject",
            )

        if authority.status not in {"ESTABLISHED", "ACTIVE"}:
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-05",
                "independent authority is not established or active",
            )

        if not authority.provenance.strip():
            return EvidenceAuthorityCheck(
                FirewallResult.INVALID,
                "K11-EVIDENCE-06",
                "independent authority has no provenance",
            )

        return EvidenceAuthorityCheck(
            FirewallResult.VALID,
            "K11-EVIDENCE-01/02/03/04/05/06",
            "evidence remains evidence; independently represented authority is evaluated separately",
        )
