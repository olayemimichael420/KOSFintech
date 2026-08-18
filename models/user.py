from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    tenant_id: str
    name: str
    email: Optional[str]
    role: str
    status: str = "active"
