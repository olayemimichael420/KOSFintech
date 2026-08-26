import json
from typing import Optional

from models.audit_event import AuditEvent


class AuditEventRepository:
    """Persistence boundary for immutable audit events."""

    def __init__(self, connection):
        self.connection = connection

    def create(self, event: AuditEvent) -> AuditEvent:
        cursor = self.connection.execute(
            """
            INSERT INTO audit_events (
                timestamp,
                event_type,
                actor_id,
                tenant_id,
                action,
                metadata
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp,
                event.event_type,
                event.actor_id,
                event.tenant_id,
                event.action,
                json.dumps(event.metadata, default=str),
            ),
        )

        self.connection.commit()

        return self.get(cursor.lastrowid)

    def get(self, event_id: int) -> Optional[AuditEvent]:
        row = self.connection.execute(
            """
            SELECT
                id,
                timestamp,
                event_type,
                actor_id,
                tenant_id,
                action,
                metadata
            FROM audit_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[AuditEvent]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                timestamp,
                event_type,
                actor_id,
                tenant_id,
                action,
                metadata
            FROM audit_events
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> AuditEvent:
        return AuditEvent(
            id=row["id"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            actor_id=row["actor_id"],
            tenant_id=row["tenant_id"],
            action=row["action"],
            metadata=json.loads(row["metadata"] or "{}"),
        )
