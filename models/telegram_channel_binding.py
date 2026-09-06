from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramChannelBinding:
    id: Optional[int]
    provider: str
    chat_id: str
    tenant_id: str
    administration_id: int
    binding_type: str
    status: str = "active"
    created_at: Optional[str] = None
