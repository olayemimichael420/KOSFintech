"""
Audit logging foundation.

All consequential operations, including AI-driven actions,
are recorded as structured log events and persisted to the
audit_events database table.

The public audit_event() API intentionally remains stable so
existing application services do not need to change.
"""

import json
import logging
from datetime import datetime, timezone

from database import get_connection
from models.audit_event import AuditEvent
from repositories.audit_event_repository import AuditEventRepository


logger = logging.getLogger("kosfintech.audit")


def audit_event(
    event_type: str,
    actor_id=None,
    tenant_id=None,
    action=None,
    metadata=None,
    connection=None,
) -> None:
    """
    Record a structured and persistent audit event.

    The existing structured logging contract is preserved while
    the same event is durably persisted in audit_events.
    """

    event = AuditEvent(
        id=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        action=action,
        metadata=metadata or {},
    )

    owns_connection = connection is None
    if owns_connection:
        connection = get_connection()

    try:
        repository = AuditEventRepository(connection)
        repository.create(event, commit=owns_connection)
    finally:
        if owns_connection:
            connection.close()

    logger.info(
        "AUDIT %s",
        json.dumps(
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "tenant_id": event.tenant_id,
                "action": event.action,
                "metadata": event.metadata,
            },
            default=str,
        ),
    )
