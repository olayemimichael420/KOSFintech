from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingContentTeacherPreacherAssignment:
    """
    CMOS assignment of a TeacherPreacher to a TeachingContent item.

    This records a structural teaching/preaching content assignment.
    It does not establish ordination, ecclesiastical authority,
    spiritual rank, authorization, attendance, learning evidence,
    assessment, results, or application permission.
    """
    id: Optional[int]
    tenant_id: str
    teaching_content_id: int
    teacher_preacher_id: int
    status: str = "active"
