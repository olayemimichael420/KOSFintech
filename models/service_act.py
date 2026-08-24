from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ServiceActStatus(str, Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ServiceAct:
    id: Optional[int]
    tenant_id: str
    provider_user_id: int
    recipient_user_id: int
    title: str
    description: str
    status: ServiceActStatus = ServiceActStatus.CREATED
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
