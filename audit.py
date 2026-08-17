"""
Audit logging foundation.

All consequential operations, including AI-driven actions,
will eventually be recorded here.
"""

import json
import logging
from datetime import datetime, timezone


logger = logging.getLogger("kosfintech.audit")


def audit_event(
    event_type: str,
    actor_id=None,
    tenant_id=None,
    action=None,
    metadata=None,
) -> None:
    """Record a structured audit event."""

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor_id": actor_id,
        "tenant_id": tenant_id,
        "action": action,
        "metadata": metadata or {},
    }

    logger.info(
        "AUDIT %s",
        json.dumps(event, default=str),
    )
