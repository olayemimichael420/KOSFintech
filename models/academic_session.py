from dataclasses import dataclass
from typing import Optional


@dataclass
class AcademicSession:
    id: Optional[int]
    tenant_id: str
    name: str
    start_date: str
    end_date: str
    status: str = "active"
