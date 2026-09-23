from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SessionTeacherPreacherAssignment:
    """
    Records assignment of an existing Teacher/Preacher capacity to a
    bounded TeachingSession within the same tenant.

    This does not establish leadership, responsibility, participation,
    attendance, learning, competence, assessment, score, grade, result,
    progress, appointment, ordination, ecclesiastical authority,
    authentication, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    teacher_preacher_id: int
    teaching_session_id: int
    status: str = "active"
