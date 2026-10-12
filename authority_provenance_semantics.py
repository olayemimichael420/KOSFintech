from dataclasses import dataclass
from enum import Enum


class ProvenanceResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class AuthorityProvenanceRecord:
    provenance_id: str
    authority_id: str
    source_reference: str
    establishing_instrument: str
    issuer_reference: str
    holder_reference: str
    jurisdiction: str
    scope: frozenset
    powers: frozenset
    limits: frozenset
    status: str
    effective_basis: str
    evidence_class: str = "CONSTITUTIONAL_RECORD"


@dataclass(frozen=True)
class AuthorityProvenanceCheck:
    result: ProvenanceResult
    rule: str
    reason: str


class AuthorityProvenanceValidator:
    """Developmental validator for independently established authority provenance.

    This validator does not establish constitutional authority itself.
    It determines whether a represented authority has a sufficiently
    specified independent provenance record for further semantic evaluation.
    """

    def validate(self, record: AuthorityProvenanceRecord) -> AuthorityProvenanceCheck:
        required = {
            "provenance_id": record.provenance_id,
            "authority_id": record.authority_id,
            "source_reference": record.source_reference,
            "establishing_instrument": record.establishing_instrument,
            "issuer_reference": record.issuer_reference,
            "holder_reference": record.holder_reference,
            "jurisdiction": record.jurisdiction,
            "effective_basis": record.effective_basis,
        }

        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-01",
                "authority provenance is missing required fields: " + ", ".join(missing),
            )

        if not record.scope:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-02",
                "authority provenance does not define scope",
            )

        if not record.powers:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-03",
                "authority provenance does not define powers",
            )

        if not record.limits:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-04",
                "authority provenance does not define limits",
            )

        if record.status not in {"ESTABLISHED", "ACTIVE"}:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-05",
                "authority provenance does not establish an active or established authority state",
            )

        if record.evidence_class not in {
            "CONSTITUTIONAL_RECORD",
            "LEGAL_RECORD",
            "FOUNDING_INSTRUMENT",
        }:
            return AuthorityProvenanceCheck(
                ProvenanceResult.INVALID,
                "AP-06",
                "technical or historical evidence cannot independently establish authority provenance",
            )

        return AuthorityProvenanceCheck(
            ProvenanceResult.VALID,
            "AP-01/AP-02/AP-03/AP-04/AP-05/AP-06",
            "authority has an independently represented establishing basis, scope, powers, limits, status, and provenance",
        )
