from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class JudicialDecision:
    id: Optional[int]
    tenant_id: str
    proceeding_id: int
    judicial_authority_id: int
    decision_type: str
    decision_reason: str
    decided_at: Optional[str] = None
