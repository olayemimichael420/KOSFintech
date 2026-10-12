from dataclasses import dataclass
from enum import Enum


class SemanticResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class AuthorityBasis:
    authority_id: str
    status: str
    powers: frozenset
    jurisdiction_id: str
    scope: frozenset
    provenance: str


@dataclass(frozen=True)
class OfficeTarget:
    office_id: str
    jurisdiction_id: str
    status: str = "ACTIVE"


@dataclass(frozen=True)
class ConstitutionalSemanticCheck:
    result: SemanticResult
    rule: str
    relation_type: str
    authority_id: str
    target_id: str
    reason: str


class RelationConstitutionalSemanticValidator:
    """Developmental CK-0.1 R3 validator.

    R3 evaluates whether a particular authority has sufficient declared
    constitutional-semantic basis to exercise a relation.

    This prototype does not create authority, ratify a constitution,
    or establish operative constitutional effect.
    """

    def validate_constitutes_office(
        self,
        authority: AuthorityBasis,
        office: OfficeTarget,
    ) -> ConstitutionalSemanticCheck:
        if authority.status not in {"ESTABLISHED", "ACTIVE"}:
            return ConstitutionalSemanticCheck(
                SemanticResult.INVALID,
                "R3-ESTABLISH-01",
                "CONSTITUTES",
                authority.authority_id,
                office.office_id,
                "authority is not in an established or active state",
            )

        if not authority.provenance.strip():
            return ConstitutionalSemanticCheck(
                SemanticResult.INVALID,
                "R3-ESTABLISH-02",
                "CONSTITUTES",
                authority.authority_id,
                office.office_id,
                "authority has no declared provenance",
            )

        if "ESTABLISH_OFFICE" not in authority.powers:
            return ConstitutionalSemanticCheck(
                SemanticResult.INVALID,
                "R3-ESTABLISH-03",
                "CONSTITUTES",
                authority.authority_id,
                office.office_id,
                "authority lacks the declared power to establish an office",
            )

        if authority.jurisdiction_id != office.jurisdiction_id:
            return ConstitutionalSemanticCheck(
                SemanticResult.INVALID,
                "R3-ESTABLISH-04",
                "CONSTITUTES",
                authority.authority_id,
                office.office_id,
                "authority jurisdiction does not contain the office jurisdiction",
            )

        if authority.scope and office.office_id not in authority.scope and "*" not in authority.scope:
            return ConstitutionalSemanticCheck(
                SemanticResult.INVALID,
                "R3-ESTABLISH-05",
                "CONSTITUTES",
                authority.authority_id,
                office.office_id,
                "authority scope does not contain the target office",
            )

        return ConstitutionalSemanticCheck(
            SemanticResult.VALID,
            "R3-ESTABLISH-01/02/03/04/05",
            "CONSTITUTES",
            authority.authority_id,
            office.office_id,
            "authority has sufficient declared establishment basis for the target office",
        )
