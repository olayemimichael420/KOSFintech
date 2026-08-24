from typing import Optional

from models.service_act import ServiceAct, ServiceActStatus


class ServiceActRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, act: ServiceAct) -> ServiceAct:
        cursor = self.connection.execute(
            """
            INSERT INTO service_acts (
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                act.tenant_id,
                act.provider_user_id,
                act.recipient_user_id,
                act.title,
                act.description,
                act.status.value,
            ),
        )

        self.connection.commit()
        act.id = cursor.lastrowid

        return self.get(act.tenant_id, act.id)

    def get(
        self,
        tenant_id: str,
        act_id: int,
    ) -> Optional[ServiceAct]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                accepted_at,
                started_at,
                submitted_at,
                completed_at,
                cancelled_at,
                cancellation_reason
            FROM service_acts
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, act_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[ServiceAct]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                accepted_at,
                started_at,
                submitted_at,
                completed_at,
                cancelled_at,
                cancellation_reason
            FROM service_acts
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_provider(
        self,
        tenant_id: str,
        provider_user_id: int,
    ) -> list[ServiceAct]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                accepted_at,
                started_at,
                submitted_at,
                completed_at,
                cancelled_at,
                cancellation_reason
            FROM service_acts
            WHERE tenant_id = ?
              AND provider_user_id = ?
            ORDER BY id
            """,
            (tenant_id, provider_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_recipient(
        self,
        tenant_id: str,
        recipient_user_id: int,
    ) -> list[ServiceAct]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                accepted_at,
                started_at,
                submitted_at,
                completed_at,
                cancelled_at,
                cancellation_reason
            FROM service_acts
            WHERE tenant_id = ?
              AND recipient_user_id = ?
            ORDER BY id
            """,
            (tenant_id, recipient_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ServiceAct:
        return ServiceAct(
            id=row["id"],
            tenant_id=row["tenant_id"],
            provider_user_id=row["provider_user_id"],
            recipient_user_id=row["recipient_user_id"],
            title=row["title"],
            description=row["description"],
            status=ServiceActStatus(row["status"]),
            created_at=row["created_at"],
            accepted_at=row["accepted_at"],
            started_at=row["started_at"],
            submitted_at=row["submitted_at"],
            completed_at=row["completed_at"],
            cancelled_at=row["cancelled_at"],
            cancellation_reason=row["cancellation_reason"],
        )
