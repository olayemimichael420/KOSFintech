from dataclasses import dataclass
from enum import Enum

from identity_holder_semantics import IdentityHolderSemanticValidator, IdentityRecord
from relation_constitutional_semantics import AuthorityBasis, OfficeTarget, RelationConstitutionalSemanticValidator
from relation_semantic_validator import RelationSemanticValidator


class PipelineResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class PipelineCheck:
    result: PipelineResult
    failed_layer: str | None
    reason: str


class ConstitutionalSemanticPipeline:
    """Developmental composition of R1-R4 only.

    This pipeline validates semantic correspondence. It does not
    create constitutional authority or constitutional effect.
    """

    def __init__(self):
        self.r2 = RelationSemanticValidator()
        self.r3 = RelationConstitutionalSemanticValidator()
        self.r4 = IdentityHolderSemanticValidator()

    def check_relation(self, relation_type, source_type, target_type):
        result = self.r2.validate(relation_type, source_type, target_type)
        if result.result.value == "INVALID":
            return PipelineCheck(PipelineResult.INVALID, "R2", result.reason)
        if result.result.value == "INDETERMINATE":
            return PipelineCheck(PipelineResult.INDETERMINATE, "R2", result.reason)
        return PipelineCheck(PipelineResult.VALID, None, "R1/R2 semantic relation boundary passed")

    def check_constitutes_office(self, authority, office):
        r2 = self.check_relation("CONSTITUTES", "AUTHORITY", "OFFICE")
        if r2.result is not PipelineResult.VALID:
            return r2
        result = self.r3.validate_constitutes_office(authority, office)
        if result.result.value == "INVALID":
            return PipelineCheck(PipelineResult.INVALID, "R3", result.reason)
        if result.result.value == "INDETERMINATE":
            return PipelineCheck(PipelineResult.INDETERMINATE, "R3", result.reason)
        return PipelineCheck(PipelineResult.VALID, None, "R2 relation and R3 authority-semantic basis passed")

    def check_subject_holds_authority(self, subject, authority):
        result = self.r4.validate("HOLDS", subject, authority)
        if result.result.value == "INVALID":
            return PipelineCheck(PipelineResult.INVALID, "R4", result.reason)
        if result.result.value == "INDETERMINATE":
            return PipelineCheck(PipelineResult.INDETERMINATE, "R4", result.reason)
        return PipelineCheck(PipelineResult.VALID, None, "R4 identity/holder boundary passed")

    def check_subject_occupies_office(self, subject, office):
        result = self.r4.validate("OCCUPIES", subject, office)
        if result.result.value == "INVALID":
            return PipelineCheck(PipelineResult.INVALID, "R4", result.reason)
        if result.result.value == "INDETERMINATE":
            return PipelineCheck(PipelineResult.INDETERMINATE, "R4", result.reason)
        return PipelineCheck(PipelineResult.VALID, None, "R4 identity/office boundary passed")
