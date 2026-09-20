from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AssessmentScore:
    """
    CMOS measurable assessment outcome recorded for a membership.

    This entity records a score for a specific assessment.
    It does not establish a grade, result, progress, competence,
    qualification, attendance, learning evidence, ecclesiastical
    authority, spiritual standing, divine standing, or application
    authorization.
    """

    id: Optional[int]
    tenant_id: str
    assessment_id: int
    membership_id: int
    score: int
    scored_date: str
    remark: Optional[str] = None
