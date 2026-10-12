from dataclasses import dataclass
from enum import Enum


class SemanticResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class VisioneerSubject:
    subject_id: str
    entity_type: str = "SUBJECT"
    classification: str = "VISIONEER"


@dataclass(frozen=True)
class FoundingAuthorityReference:
    authority_id: str
    holder_id: str
    status: str
    powers: frozenset
    provenance: str


@dataclass(frozen=True)
class VisioneerSemanticCheck:
    result: SemanticResult
    rule: str
    reason: str


class VisioneerSemanticValidator:
    """Developmental test of Visioneer identity/capacity boundaries.

    VISIONEER is a classification/capacity of a SUBJECT, not an
    independent authority type. Authority must still be represented
    separately and must have its own declared basis.
    """

    def validate_subject(self, subject: VisioneerSubject) -> VisioneerSemanticCheck:
        if subject.entity_type != "SUBJECT":
            return VisioneerSemanticCheck(
                SemanticResult.INVALID,
                "V-01",
                "Visioneer must remain a SUBJECT rather than a separate authority type",
            )
        if subject.classification != "VISIONEER":
            return VisioneerSemanticCheck(
                SemanticResult.INDETERMINATE,
                "V-02",
                "subject is not classified as Visioneer",
            )
        return VisioneerSemanticCheck(
            SemanticResult.VALID,
            "V-01/V-02",
            "Visioneer is represented as a SUBJECT with VISIONEER classification",
        )

    def validate_authority_holder(
        self,
        subject: VisioneerSubject,
        authority: FoundingAuthorityReference,
    ) -> VisioneerSemanticCheck:
        subject_result = self.validate_subject(subject)
        if subject_result.result is not SemanticResult.VALID:
            return subject_result
        if authority.holder_id != subject.subject_id:
            return VisioneerSemanticCheck(
                SemanticResult.INVALID,
                "V-03",
                "authority holder does not resolve to the represented Visioneer subject",
            )
        if authority.status not in {"ESTABLISHED", "ACTIVE"}:
            return VisioneerSemanticCheck(
                SemanticResult.INVALID,
                "V-04",
                "Visioneer classification does not activate an authority whose status is not established or active",
            )
        if not authority.provenance.strip():
            return VisioneerSemanticCheck(
                SemanticResult.INVALID,
                "V-05",
                "founding authority requires independent provenance",
            )
        return VisioneerSemanticCheck(
            SemanticResult.VALID,
            "V-03/V-04/V-05",
            "Visioneer subject may hold separately represented founding authority when that authority has its own valid basis",
        )
