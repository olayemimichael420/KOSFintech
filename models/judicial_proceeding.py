from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JudicialProceedingStatus(str, Enum):
    PROPOSED = "proposed"
    OPEN = "open"
    ACTIVE = "active"
    CLOSED = "closed"
    TERMINATED = "terminated"


@dataclass(frozen=True)
class JudicialProceeding:
    id: Optional[int]
    tenant_id: str
    dispute_id: int
    jurisdiction_id: int
    proceeding_type: str
    status: JudicialProceedingStatus = JudicialProceedingStatus.PROPOSED
    opened_by_authority_id: Optional[int] = None
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None
    closure_reason: Optional[str] = None
