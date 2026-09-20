from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LearningEvidence:
    """
    CMOS observable learning-evidence record for a church membership
    associated with teaching content.

    This entity records observable evidence. It does not establish
    attendance, assessment, score, grade, result, progress, competence,
    qualification, ecclesiastical authority, spiritual standing,
    divine standing, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    membership_id: int
    teaching_content_id: int
    evidence_date: str
    description: str
    remark: Optional[str] = None
