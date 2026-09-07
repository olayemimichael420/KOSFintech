from typing import Optional

from models.service_request import ServiceRequest, ServiceRequestStatus


class ServiceRequestRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        request: ServiceRequest,
        commit: bool = True,
    ) -> ServiceRequest:
        cursor = self.connection.execute(
            """
            INSERT INTO service_requests (
                tenant_id,
                requester_user_id,
                recipient_user_id,
                title,
                description,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.tenant_id,
                request.requester_user_id,
                request.recipient_user_id,
                request.title,
                request.description,
                request.status.value,
            ),
        )

        if commit:
            self.connection.commit()

        request_id = cursor.lastrowid
        return self.get(request.tenant_id, request_id)

    def get(
        self,
        tenant_id: str,
        request_id: int,
    ) -> Optional[ServiceRequest]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                requester_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                authorized_at,
                cancelled_at,
                cancellation_reason
            FROM service_requests
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, request_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[ServiceRequest]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                requester_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                authorized_at,
                cancelled_at,
                cancellation_reason
            FROM service_requests
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_requester(
        self,
        tenant_id: str,
        requester_user_id: int,
    ) -> list[ServiceRequest]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                requester_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                authorized_at,
                cancelled_at,
                cancellation_reason
            FROM service_requests
            WHERE tenant_id = ?
              AND requester_user_id = ?
            ORDER BY id
            """,
            (tenant_id, requester_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_recipient(
        self,
        tenant_id: str,
        recipient_user_id: int,
    ) -> list[ServiceRequest]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                requester_user_id,
                recipient_user_id,
                title,
                description,
                status,
                created_at,
                authorized_at,
                cancelled_at,
                cancellation_reason
            FROM service_requests
            WHERE tenant_id = ?
              AND recipient_user_id = ?
            ORDER BY id
            """,
            (tenant_id, recipient_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ServiceRequest:
        return ServiceRequest(
            id=row["id"],
            tenant_id=row["tenant_id"],
            requester_user_id=row["requester_user_id"],
            recipient_user_id=row["recipient_user_id"],
            title=row["title"],
            description=row["description"],
            status=ServiceRequestStatus(row["status"]),
            created_at=row["created_at"],
            authorized_at=row["authorized_at"],
            cancelled_at=row["cancelled_at"],
            cancellation_reason=row["cancellation_reason"],
        )
