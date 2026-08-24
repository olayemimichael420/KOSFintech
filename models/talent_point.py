from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TalentPointTransaction:
    id: Optional[int]
    tenant_id: str
    user_id: int
    service_act_id: int
    amount: int
    transaction_type: str
    created_at: Optional[datetime] = None
    reference: Optional[str] = None
