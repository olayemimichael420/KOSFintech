from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChurchProgram:
    """
    CMOS church-program domain entity.

    This represents an operational program within a tenant.
    It does not establish institutional provenance, confer
    ecclesiastical authority, or grant KOSFintech authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    description: Optional[str] = None
    program_type: Optional[str] = None
    status: str = "active"
