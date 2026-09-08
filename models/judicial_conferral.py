from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class JudicialConferral:
    id: Optional[int]
    appointment_id: int
    authority_id: int
    conferring_authority: str
    conferral_instrument: str
    conferral_date: Optional[datetime] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    status: str = "active"
