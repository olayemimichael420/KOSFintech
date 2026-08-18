from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Administration:
    """
    General administrative tenant.

    An administration may represent a school, hospital, church,
    hotel, community, company, association, or another
    organizational domain.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    administration_type: str
    status: str = "active"
    created_at: Optional[datetime] = None
