from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TeachingFocus:
    """
    CMOS teaching/preaching focus.

    Represents a bounded teaching/preaching focus within a teaching
    series. It does not establish teaching capacity, assignment,
    attendance, participation, ecclesiastical authority, or
    application authorization.
    """

    id: Optional[int]
    tenant_id: str
    teaching_series_id: int
    name: str
    start_date: str
    end_date: str
    status: str = "active"
