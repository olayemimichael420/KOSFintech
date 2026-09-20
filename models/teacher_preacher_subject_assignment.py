from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeacherPreacherSubjectAssignment:
    """
    CMOS teaching/preaching subject assignment.

    Represents an assignment of a TeacherPreacher capacity to a
    reusable TeachingSubject within a tenant.

    This entity does not establish membership, authentication,
    application authorization, ecclesiastical authority, ordination,
    appointment, attendance, participation, or permission.
    """

    id: Optional[int]
    tenant_id: str
    teacher_preacher_id: int
    teaching_subject_id: int
    status: str = "active"
