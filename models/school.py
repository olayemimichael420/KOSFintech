from dataclasses import dataclass
from typing import Optional


@dataclass
class School:
    tenant_id: str
    name: str
    school_type: str
    country: str
    currency: str
    created_at: Optional[str] = None
