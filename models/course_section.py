from dataclasses import dataclass
from typing import Optional


@dataclass
class CourseSection:
    id: Optional[int]
    tenant_id: str
    course_offering_id: int
    name: str
    status: str = "active"
