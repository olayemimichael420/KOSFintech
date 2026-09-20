from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Membership:
    """
    Institutional membership relationship between a Person and a
    ChurchAnchor within a KOSFintech tenant.

    Membership does not establish authentication, application
    authorization, leadership, teaching capacity, attendance,
    participation, or ecclesiastical authority.
    """

    id: Optional[int]
    tenant_id: str
    person_id: int
    church_anchor_id: int
    membership_status: str = "active"
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    provenance_reference: str = ""
    created_at: Optional[str] = None
