from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TeacherPreacherRole(str, Enum):
    TEACHER = "teacher"
    PREACHER = "preacher"
    TEACHER_PREACHER = "teacher_preacher"


@dataclass(frozen=True)
class TeacherPreacher:
    """
    CMOS teaching/preaching capacity associated with a Person.

    This entity identifies a person's teaching/preaching capacity within
    a tenant. It does not establish membership, authentication,
    application authorization, ecclesiastical authority, ordination,
    appointment, assignment, attendance, participation, or permission.
    """

    id: Optional[int]
    tenant_id: str
    person_id: int
    role: TeacherPreacherRole
    status: str = "active"
