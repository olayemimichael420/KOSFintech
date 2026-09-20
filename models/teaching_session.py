from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingSession:
    """
    CMOS teaching session.

    Represents a bounded teaching/preaching period within a tenant.
    It does not establish church-program membership, teaching capacity,
    assignment, attendance, participation, ecclesiastical authority,
    or application authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    start_date: str
    end_date: str
    status: str = "active"
