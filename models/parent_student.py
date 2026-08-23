from dataclasses import dataclass


@dataclass
class ParentStudentLink:
    tenant_id: str
    parent_id: int
    student_id: int
