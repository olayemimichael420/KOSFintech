from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingContent:
    """
    CMOS teaching/preaching content.

    Represents an ordered content item within a teaching focus.
    It does not establish teaching capacity, assignment, attendance,
    participation, learning evidence, assessment, results,
    ecclesiastical authority, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    teaching_focus_id: int
    name: str
    description: Optional[str] = None
    sequence: Optional[int] = None
    status: str = "active"
