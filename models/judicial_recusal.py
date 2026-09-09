from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JudicialRecusalStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class JudicialRecusalScope(str, Enum):
    JURISDICTION = "jurisdiction"
    PROCEEDING = "proceeding"


@dataclass(frozen=True)
class JudicialRecusal:
    id: Optional[int]
    tenant_id: str
    judicial_authority_id: int
    jurisdiction_id: int
    scope: JudicialRecusalScope
    reason: str
    initiated_by: int
    proceeding_id: Optional[int] = None
    recorded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    status: JudicialRecusalStatus = JudicialRecusalStatus.ACTIVE
