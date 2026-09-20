from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChurchActivityStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    APPROVED = "approved"
    LIVE = "live"
    DELIVERED = "delivered"
    RECORDED = "recorded"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class ChurchActivityDeliveryMode(str, Enum):
    PHYSICAL = "physical"
    ONLINE = "online"
    LIVE_STREAM = "live_stream"
    HYBRID = "hybrid"
    RECORDED = "recorded"
    ON_DEMAND = "on_demand"


@dataclass(frozen=True)
class ChurchActivity:
    """
    CMOS generalized church-activity domain entity.

    Represents an operational activity within a tenant.
    It does not establish institutional provenance,
    ecclesiastical authority, spiritual standing,
    or KOSFintech application authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    description: Optional[str] = None
    activity_type: str = ""
    purpose: Optional[str] = None
    program_id: Optional[int] = None
    status: ChurchActivityStatus = ChurchActivityStatus.DRAFT
    delivery_mode: ChurchActivityDeliveryMode = (
        ChurchActivityDeliveryMode.PHYSICAL
    )
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    created_at: Optional[str] = None
