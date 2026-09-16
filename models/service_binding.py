from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ServiceBinding:
    """
    Service relationship between an established institution and a
    KOSFintech tenant.

    This records service connectivity only. It does not confer
    institutional authority, KOSFintech authorization, ownership,
    or administrative authority.
    """

    id: Optional[int]
    institution_anchor_id: int
    tenant_id: str
    status: str = "active"
    created_at: Optional[str] = None
