from dataclasses import dataclass
from typing import Optional


@dataclass
class CourseOffering:
    id: Optional[int]
    tenant_id: str
    academic_class_id: int
    academic_subject_id: int
    academic_session_id: int
    academic_term_id: int
    status: str = "active"
