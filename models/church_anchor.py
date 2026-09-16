from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChurchAnchor:
    """
    Externally established Church / denomination identity anchor.

    This records a Church identity and its external provenance reference
    for KOSFintech service binding. It does not confer ecclesiastical
    authority or KOSFintech authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    provenance_reference: str
    verification_status: str = "pending"
    status: str = "active"
    created_at: Optional[str] = None
