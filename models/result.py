from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Result:
    """
    CMOS recorded learning outcome associated with an assessment.

    This entity records an outcome for a membership in relation to an
    assessment and its grade classification.

    It does not establish a score, grade definition, progress, competence,
    qualification, attendance, learning evidence, ecclesiastical authority,
    spiritual standing, divine standing, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    assessment_id: int
    membership_id: int
    grade_id: int
    result: str
    result_date: str
    remark: Optional[str] = None
    status: str = "active"
