from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class InstitutionAnchor:
    """
    Externally established institutional identity anchor.

    This records institutional identity and its external provenance
    reference. It does not create a KOSFintech tenant, confer
    authority, or grant authorization.
    """

    id: Optional[int]
    institution_type: str
    name: str
    provenance_reference: str
    verification_status: str = "pending"
    status: str = "active"
    created_at: Optional[str] = None
