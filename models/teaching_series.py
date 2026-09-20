from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingSeries:
    """
    CMOS teaching series.

    Represents a bounded series of teaching/preaching activity
    within a teaching session. It does not establish teaching
    capacity, assignment, attendance, participation, ecclesiastical
    authority, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    teaching_session_id: int
    name: str
    start_date: str
    end_date: str
    status: str = "active"
