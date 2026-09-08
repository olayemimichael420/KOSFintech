from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class JudicialAction:
    id: Optional[int]
    tenant_id: str
    proceeding_id: int
    judicial_authority_id: int
    action_type: str
    action_details: str
    acted_at: Optional[str] = None
