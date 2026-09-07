from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ServiceRequestStatus(str, Enum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ServiceRequest:
    id: Optional[int]
    tenant_id: str
    requester_user_id: int
    recipient_user_id: int
    title: str
    description: str
    status: ServiceRequestStatus = ServiceRequestStatus.REQUESTED
    created_at: Optional[str] = None
    authorized_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
