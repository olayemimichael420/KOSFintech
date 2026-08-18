from dataclasses import dataclass
from typing import Optional


@dataclass
class Parent:
    id: Optional[int]
    tenant_id: str
    user_id: Optional[int]
    name: str
    phone: Optional[str]
    email: Optional[str]
    status: str = "active"
