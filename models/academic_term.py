from dataclasses import dataclass
from typing import Optional


@dataclass
class AcademicTerm:
    id: Optional[int]
    tenant_id: str
    academic_session_id: int
    name: str
    start_date: str
    end_date: str
    status: str = "active"
