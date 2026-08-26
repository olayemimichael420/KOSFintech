from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class AuditEvent:
    """Immutable persisted audit event."""

    id: Optional[int]
    timestamp: str
    event_type: str
    actor_id: Optional[int]
    tenant_id: Optional[str]
    action: Optional[str]
    metadata: dict[str, Any]
