from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    id: Optional[int]
    tenant_id: str
    user_id: Optional[int]
    name: str
    class_name: str
    age: Optional[int]
    guardian_id: Optional[int]
    enrollment_date: Optional[str]
    status: str = "active"
