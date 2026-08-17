from dataclasses import dataclass


@dataclass
class ParentStudentLink:
    parent_id: int
    student_id: int
