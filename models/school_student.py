from dataclasses import dataclass


@dataclass
class SchoolStudentLink:
    tenant_id: str
    student_id: int
