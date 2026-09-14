from dataclasses import dataclass
from typing import Optional


@dataclass
class SectionStudentEnrollment:
    id: Optional[int]
    tenant_id: str
    course_section_id: int
    student_id: int
    status: str = "active"
