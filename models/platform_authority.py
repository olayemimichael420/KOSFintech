from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PlatformAuthorityRole(str, Enum):
    SUPER_ADMIN = "super_admin"


@dataclass(frozen=True)
class PlatformAuthority:
    id: Optional[int]
    user_id: int
    role: PlatformAuthorityRole
    status: str = "active"
    created_at: Optional[datetime] = None
    transferred_at: Optional[datetime] = None
