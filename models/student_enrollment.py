from dataclasses import dataclass
from typing import Optional


@dataclass
class StudentEnrollment:
    id: Optional[int]
    tenant_id: str
    student_id: int
    academic_class_id: int
    academic_session_id: int
    academic_term_id: Optional[int]
    enrollment_date: Optional[str]
    status: str = "active"
