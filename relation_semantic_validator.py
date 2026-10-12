from dataclasses import dataclass
from enum import Enum


class SemanticResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class RelationSemanticCheck:
    result: SemanticResult
    rule: str
    relation_type: str
    source_type: str
    target_type: str
    reason: str


R2_RELATION_MATRIX = {
    "DERIVES_FROM": {( "MANDATE", "SOURCE"), ("AUTHORITY", "SOURCE"), ("AUTHORITY", "MANDATE")},
    "MANDATES": {("SOURCE", "MANDATE"), ("SOURCE", "SUBJECT"), ("MANDATE", "SUBJECT")},
    "CONSTITUTES": {("SOURCE", "OFFICE"), ("AUTHORITY", "OFFICE"), ("MANDATE", "OFFICE")},
    "HOLDS": {("SUBJECT", "AUTHORITY")},
    "OCCUPIES": {("SUBJECT", "OFFICE")},
    "APPLIES_TO": {("AUTHORITY", "JURISDICTION"), ("ACTION", "JURISDICTION")},
    "DELEGATES": {("AUTHORITY", "AUTHORITY")},
    "AUTHORIZES": {("AUTHORITY", "ACTION")},
    "LIMITS": {("AUTHORITY", "AUTHORITY"), ("AUTHORITY", "ACTION"), ("OFFICE", "AUTHORITY")},
    "REQUIRES": {("AUTHORITY", "MANDATE"), ("ACTION", "AUTHORITY"), ("OFFICE", "AUTHORITY")},
    "PERFORMS": {("SUBJECT", "ACTION")},
    "VERIFIES": {("SUBJECT", "ACTION"), ("AUTHORITY", "ACTION")},
    "SUCCEEDS": {("SUBJECT", "SUBJECT"), ("OFFICE", "OFFICE"), ("AUTHORITY", "AUTHORITY")},
}


class RelationSemanticValidator:
    """Developmental CK-0.1 R2 validator.

    Validates only semantic source/target type compatibility.
    It does not establish constitutional authority or authorization.
    """

    def validate(self, relation_type, source_type: str, target_type: str) -> RelationSemanticCheck:
        relation = getattr(relation_type, "value", relation_type)
        if relation not in R2_RELATION_MATRIX:
            return RelationSemanticCheck(
                SemanticResult.INDETERMINATE,
                "R2",
                str(relation),
                source_type,
                target_type,
                "relation type has no currently admitted R2 semantic rule",
            )

        pair = (source_type, target_type)
        if pair not in R2_RELATION_MATRIX[relation]:
            return RelationSemanticCheck(
                SemanticResult.INVALID,
                "R2",
                relation,
                source_type,
                target_type,
                "source/target semantic types are not admitted for this relation",
            )

        return RelationSemanticCheck(
            SemanticResult.VALID,
            "R2",
            relation,
            source_type,
            target_type,
            "source/target semantic types are admitted for this relation",
        )
