from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ReputationEvent:
    id: Optional[int]
    tenant_id: str
    service_act_id: int
    subject_user_id: int
    reviewer_user_id: int
    score: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
