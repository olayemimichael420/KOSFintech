from dataclasses import dataclass
from typing import Optional


@dataclass
class Permission:
    id: Optional[int]
    tenant_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
