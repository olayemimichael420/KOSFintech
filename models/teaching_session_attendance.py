from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingSessionAttendance:
    """
    CMOS attendance record for a church membership within a teaching session.

    Attendance is an observable operational record. It does not establish
    participation, learning, competence, assessment, result, progress,
    ecclesiastical authority, spiritual standing, or divine standing.
    """

    id: Optional[int]
    tenant_id: str
    teaching_session_id: int
    membership_id: int
    attendance_date: str
    status: str = "present"
    remark: Optional[str] = None
