from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Assessment:
    """
    CMOS assessment record associated with teaching content.

    This entity represents an intentional evaluation activity.
    It does not establish a score, grade, result, progress,
    competence, qualification, attendance, learning evidence,
    ecclesiastical authority, spiritual standing, divine standing,
    or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    teaching_content_id: int
    name: str
    description: Optional[str] = None
    assessment_date: str = ""
    status: str = "active"
