from typing import Optional

from models.dispute import (
    Dispute,
    DisputeInitiatorRole,
    DisputeResolution,
    DisputeStatus,
)


class DisputeRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, dispute: Dispute) -> Dispute:
        cursor = self.connection.execute(
            """
            INSERT INTO disputes (
                tenant_id,
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status,
                resolution,
                resolution_reason,
                resolved_by_user_id,
                resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dispute.tenant_id,
                dispute.service_act_id,
                dispute.initiator_user_id,
                dispute.initiator_role.value,
                dispute.reason,
                dispute.status.value,
                dispute.resolution.value if dispute.resolution else None,
                dispute.resolution_reason,
                dispute.resolved_by_user_id,
                dispute.resolved_at,
            ),
        )

        self.connection.commit()



        return self.get(dispute.tenant_id, cursor.lastrowid)

    def get(
        self,
        tenant_id: str,
        dispute_id: int,
    ) -> Optional[Dispute]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status,
                resolution,
                resolution_reason,
                resolved_by_user_id,
                created_at,
                resolved_at
            FROM disputes
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, dispute_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[Dispute]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status,
                resolution,
                resolution_reason,
                resolved_by_user_id,
                created_at,
                resolved_at
            FROM disputes
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_service_act(
        self,
        tenant_id: str,
        service_act_id: int,
    ) -> list[Dispute]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                initiator_user_id,
                reason,
                initiator_role,
                status,
                resolution,
                resolution_reason,
                resolved_by_user_id,
                created_at,
                resolved_at
            FROM disputes
            WHERE tenant_id = ?
              AND service_act_id = ?
            ORDER BY id
            """,
            (tenant_id, service_act_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_initiator(
        self,
        tenant_id: str,
        initiator_user_id: int,
    ) -> list[Dispute]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status,
                resolution,
                resolution_reason,
                resolved_by_user_id,
                created_at,
                resolved_at
            FROM disputes
            WHERE tenant_id = ?
              AND initiator_user_id = ?
            ORDER BY id
            """,
            (tenant_id, initiator_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Dispute:
        return Dispute(
            id=row["id"],
            tenant_id=row["tenant_id"],
            service_act_id=row["service_act_id"],
            initiator_user_id=row["initiator_user_id"],
            initiator_role=DisputeInitiatorRole(row["initiator_role"]),
            reason=row["reason"],
            status=DisputeStatus(row["status"]),
            resolution=(
                DisputeResolution(row["resolution"])
                if row["resolution"] is not None
                else None
            ),
            resolution_reason=row["resolution_reason"],
            resolved_by_user_id=row["resolved_by_user_id"],
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
        )
