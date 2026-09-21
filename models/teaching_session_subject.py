from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingSessionSubject:
    """
    CMOS teaching-session subject offering.

    Represents a reusable teaching subject offered within a bounded
    teaching session for a tenant.

    It does not establish teaching capacity, assignment, attendance,
    participation, learning evidence, assessment, results,
    ecclesiastical authority, or application authorization.
    """
    id: Optional[int]
    tenant_id: str
    teaching_session_id: int
    teaching_subject_id: int
    status: str = "active"
