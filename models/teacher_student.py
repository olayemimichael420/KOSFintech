from dataclasses import dataclass


@dataclass
class TeacherStudentLink:
    tenant_id: str
    teacher_id: int
    student_id: int
