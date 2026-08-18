from dataclasses import dataclass
from typing import Optional


@dataclass
class Role:
    id: Optional[int]
    tenant_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
