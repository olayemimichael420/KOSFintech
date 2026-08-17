from dataclasses import dataclass
from typing import Optional


@dataclass
class SchoolAdmin:
    id: Optional[int]
    tenant_id: str
    user_id: int
    role: str
    phone: str
    email: Optional[str] = None
    verified: bool = False
    verification_code: Optional[str] = None
    code_expires: Optional[str] = None
    created_at: Optional[str] = None
