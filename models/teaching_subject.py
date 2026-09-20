from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingSubject:
    """
    CMOS teaching/preaching subject.

    Represents a reusable tenant-scoped teaching subject identity.
    It does not establish teaching capacity, assignment, attendance,
    participation, ecclesiastical authority, or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    status: str = "active"
