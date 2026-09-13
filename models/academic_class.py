from dataclasses import dataclass
from typing import Optional


@dataclass
class AcademicClass:
    id: Optional[int]
    tenant_id: str
    name: str
    education_level: Optional[str] = None
    sequence: Optional[int] = None
    status: str = "active"
