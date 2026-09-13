from dataclasses import dataclass
from typing import Optional


@dataclass
class SectionTeacherAssignment:
    id: Optional[int]
    tenant_id: str
    course_section_id: int
    teacher_id: int
    status: str = "active"
