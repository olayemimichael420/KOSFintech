from dataclasses import dataclass
from typing import Optional


@dataclass
class TeacherSubjectAssignment:
    id: Optional[int]
    tenant_id: str
    teacher_id: int
    academic_subject_id: int
    status: str = "active"
