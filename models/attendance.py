from dataclasses import dataclass
from typing import Optional


@dataclass
class Attendance:
    id: Optional[int]
    tenant_id: str
    student_id: int
    attendance_date: str
    status: str = "present"
    remark: Optional[str] = None
