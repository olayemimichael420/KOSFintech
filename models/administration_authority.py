from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AdministrationAuthorityRole(str, Enum):
    OWNER = "owner"
    ADMIN_1 = "admin1"
    ADMIN_2 = "admin2"


@dataclass(frozen=True)
class AdministrationAuthority:
    id: Optional[int]
    administration_id: int
    user_id: int
    role: AdministrationAuthorityRole
    status: str = "active"
    created_at: Optional[datetime] = None
