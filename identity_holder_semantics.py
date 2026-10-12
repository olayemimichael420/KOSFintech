from dataclasses import dataclass
from enum import Enum


class SemanticResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class IdentityRecord:
    entity_id: str
    entity_type: str
    classification: str = ""


@dataclass(frozen=True)
class HolderSemanticCheck:
    result: SemanticResult
    rule: str
    relation_type: str
    source_id: str
    target_id: str
    reason: str


class IdentityHolderSemanticValidator:
    """Developmental identity/holder boundary validator.

    Distinguishes person/subject identity, office, authority and
    technical capability. It does not grant constitutional authority.
    """

    def validate(self, relation_type: str, source: IdentityRecord, target: IdentityRecord) -> HolderSemanticCheck:
        if relation_type == "HOLDS":
            if source.entity_type != "SUBJECT" or target.entity_type != "AUTHORITY":
                return HolderSemanticCheck(
                    SemanticResult.INVALID,
                    "R4-HOLDS-01",
                    relation_type,
                    source.entity_id,
                    target.entity_id,
                    "HOLDS requires SUBJECT as source and AUTHORITY as target",
                )
            return HolderSemanticCheck(
                SemanticResult.VALID,
                "R4-HOLDS-01",
                relation_type,
                source.entity_id,
                target.entity_id,
                "subject may be represented as holder of an authority without identity being converted into authority",
            )

        if relation_type == "OCCUPIES":
            if source.entity_type != "SUBJECT" or target.entity_type != "OFFICE":
                return HolderSemanticCheck(
                    SemanticResult.INVALID,
                    "R4-OCCUPIES-01",
                    relation_type,
                    source.entity_id,
                    target.entity_id,
                    "OCCUPIES requires SUBJECT as source and OFFICE as target",
                )
            return HolderSemanticCheck(
                SemanticResult.VALID,
                "R4-OCCUPIES-01",
                relation_type,
                source.entity_id,
                target.entity_id,
                "subject may occupy an office without becoming the office itself",
            )

        if relation_type == "PERFORMS":
            if source.entity_type != "SUBJECT" or target.entity_type != "ACTION":
                return HolderSemanticCheck(
                    SemanticResult.INVALID,
                    "R4-PERFORMS-01",
                    relation_type,
                    source.entity_id,
                    target.entity_id,
                    "PERFORMS requires SUBJECT as source and ACTION as target",
                )
            return HolderSemanticCheck(
                SemanticResult.VALID,
                "R4-PERFORMS-01",
                relation_type,
                source.entity_id,
                target.entity_id,
                "subject may perform an action without identity itself becoming authority",
            )

        return HolderSemanticCheck(
            SemanticResult.INDETERMINATE,
            "R4-UNRESOLVED-01",
            relation_type,
            source.entity_id,
            target.entity_id,
            "holder semantics for this relation are not established by the R4 prototype",
        )
