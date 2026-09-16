from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Tenant:
    """
    KOSFintech service-isolation boundary.

    A tenant identifies the service boundary within which
    KOSFintech data is isolated.

    A tenant does not establish institutional provenance,
    confer authority, create administrative authority,
    or grant authorization.
    """
    id: Optional[int]
    tenant_id: str
    status: str = "active"
