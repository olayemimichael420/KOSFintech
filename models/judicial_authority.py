from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JudicialAuthorityStatus(str, Enum):
    PROPOSED = "proposed"
    VETTED = "vetted"
    APPOINTED = "appointed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True)
class JudicialAuthority:
    id: Optional[int]
    user_id: int
    authority_type: str
    jurisdiction_id: int
    judicial_level: str
    appointment_id: int
    conferral_id: int
    status: JudicialAuthorityStatus = JudicialAuthorityStatus.PROPOSED
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
