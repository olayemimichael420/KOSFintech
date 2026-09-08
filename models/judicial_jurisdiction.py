from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JudicialJurisdictionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class JudicialJurisdiction:
    id: Optional[int]
    tenant_id: str
    jurisdiction_type: str
    jurisdiction_scope: str
    judicial_level: str
    case_types: str
    parent_jurisdiction_id: Optional[int] = None
    status: JudicialJurisdictionStatus = JudicialJurisdictionStatus.ACTIVE
