from dataclasses import dataclass
from typing import Optional


@dataclass
class AcademicSubject:
    id: Optional[int]
    tenant_id: str
    name: str
    status: str = "active"
