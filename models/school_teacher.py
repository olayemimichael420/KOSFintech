from dataclasses import dataclass


@dataclass
class SchoolTeacherLink:
    tenant_id: str
    teacher_id: int
