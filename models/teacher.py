from dataclasses import dataclass
from typing import Optional


@dataclass
class Teacher:
    id: Optional[int]
    tenant_id: str
    user_id: Optional[int]
    name: str
    subject: str
    qualification: Optional[str]
    status: str = "active"
