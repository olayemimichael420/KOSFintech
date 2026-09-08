from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class JudicialAppointment:
    id: Optional[int]
    candidate_user_id: int
    jurisdiction_id: int
    judicial_level: str
    appointment_source: str
    appointment_basis: str
    qualification_record: str
    appointed_by: int
    appointed_at: Optional[datetime] = None
    term_start: Optional[datetime] = None
    term_end: Optional[datetime] = None
    status: str = "appointed"
