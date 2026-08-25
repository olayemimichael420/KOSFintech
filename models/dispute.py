from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class DisputeInitiatorRole(str, Enum):
    PROVIDER = "provider"
    RECIPIENT = "recipient"


class DisputeResolution(str, Enum):
    PROVIDER_FAVORED = "provider_favored"
    RECIPIENT_FAVORED = "recipient_favored"
    MUTUAL_SETTLEMENT = "mutual_settlement"
    NO_FAULT = "no_fault"


@dataclass(frozen=True)
class Dispute:
    id: Optional[int]
    tenant_id: str
    service_act_id: int
    initiator_user_id: int
    initiator_role: DisputeInitiatorRole
    reason: str
    status: DisputeStatus = DisputeStatus.OPEN
    resolution: Optional[DisputeResolution] = None
    resolution_reason: Optional[str] = None
    resolved_by_user_id: Optional[int] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
