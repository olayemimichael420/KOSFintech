from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Progress:
    """
    CMOS recorded learning progress associated with a membership
    and teaching content.

    This entity records an observable development or change over time.
    It does not establish a score, grade, result, competence,
    qualification, attendance, learning evidence, ecclesiastical
    authority, spiritual standing, divine standing, or application
    authorization.
    """

    id: Optional[int]
    tenant_id: str
    membership_id: int
    teaching_content_id: int
    progress_date: str
    description: str
    remark: Optional[str] = None
    status: str = "active"
