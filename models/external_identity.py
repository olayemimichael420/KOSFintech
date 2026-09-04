from dataclasses import dataclass
from typing import Optional


@dataclass
class ExternalIdentity:
    id: Optional[int]
    provider: str
    subject: str
    tenant_id: str
    user_id: int
    created_at: Optional[str] = None
