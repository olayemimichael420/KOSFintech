from datetime import datetime, timezone
from audit import audit_event

from models.service_request import ServiceRequestStatus
from services.permission_resolution_service import PermissionResolutionService


class ServiceRequestService:
    """Application service responsible for Service Request lifecycle."""

    WRITE_PERMISSION = "service_request.write"

    _TRANSITIONS = {
        ServiceRequestStatus.REQUESTED: {
            ServiceRequestStatus.AUTHORIZED,
            ServiceRequestStatus.CANCELLED,
        },
        ServiceRequestStatus.AUTHORIZED: set(),
        ServiceRequestStatus.CANCELLED: set(),
    }

    def __init__(
        self,
        repository,
        permission_service: PermissionResolutionService,
    ):
        self.repository = repository
        self.permission_service = permission_service

    def create(
        self,
        request,
        actor_id: int | None = None,
        commit: bool = True,
    ):
        """Create a Service Request for the authorized tenant context."""
        if actor_id is None:
            raise PermissionError("service request actor is required")

        if not self.permission_service.has_permission(
            user_id=actor_id,
            permission_name=self.WRITE_PERMISSION,
            tenant_id=request.tenant_id,
        ):
            raise PermissionError("service request permission denied")

        if actor_id != request.requester_user_id:
            raise PermissionError(
                "service request actor is not the requester"
            )

        if request.requester_user_id == request.recipient_user_id:
            raise ValueError(
                "service request requester and recipient must differ"
            )

        connection = self.repository.connection

        if commit:
            try:
                connection.execute("BEGIN")
                created = self.repository.create(request, commit=False)
                audit_event(
                    event_type="service_request_created",
                    actor_id=actor_id,
                    tenant_id=request.tenant_id,
                    action="create_service_request",
                    metadata={"service_request_id": created.id},
                    connection=connection,
                )
                connection.commit()
                return created
            except Exception:
                connection.rollback()
                raise

        created = self.repository.create(request, commit=False)
        audit_event(
            event_type="service_request_created",
            actor_id=actor_id,
            tenant_id=request.tenant_id,
            action="create_service_request",
            metadata={"service_request_id": created.id},
            connection=connection,
        )
        return created

    def transition(
        self,
        tenant_id: str,
        request_id: int,
        target_status: ServiceRequestStatus,
        cancellation_reason: str | None = None,
        commit: bool = True,
        actor_id: int | None = None,
    ):
        """Execute an externally authorized Service Request transition."""
        if actor_id is None:
            raise PermissionError("service request actor is required")

        if not self.permission_service.has_permission(
            user_id=actor_id,
            permission_name=self.WRITE_PERMISSION,
            tenant_id=tenant_id,
        ):
            raise PermissionError("service request permission denied")

        request = self.repository.get(tenant_id, request_id)

        if request is None:
            raise ValueError("service request not found")

        if not self._actor_can_perform_transition(
            request,
            target_status,
            actor_id,
        ):
            raise PermissionError(
                "service request actor is not authorized for this transition"
            )

        return self._apply_transition(
            tenant_id=tenant_id,
            request_id=request_id,
            target_status=target_status,
            cancellation_reason=cancellation_reason,
            commit=commit,
            actor_id=actor_id,
        )

    def _actor_can_perform_transition(
        self,
        request,
        target_status: ServiceRequestStatus,
        actor_id: int,
    ) -> bool:
        if target_status == ServiceRequestStatus.AUTHORIZED:
            return actor_id == request.requester_user_id

        if target_status == ServiceRequestStatus.CANCELLED:
            return actor_id == request.requester_user_id

        return False

    def _apply_transition(
        self,
        tenant_id: str,
        request_id: int,
        target_status: ServiceRequestStatus,
        cancellation_reason: str | None = None,
        commit: bool = True,
        actor_id: int | None = None,
    ):
        request = self.repository.get(tenant_id, request_id)

        if request is None:
            raise ValueError("service request not found")

        if target_status not in self._TRANSITIONS[request.status]:
            raise ValueError(
                f"invalid service request transition: "
                f"{request.status.value} -> {target_status.value}"
            )

        if (
            target_status == ServiceRequestStatus.CANCELLED
            and not cancellation_reason
        ):
            raise ValueError("cancellation reason is required")

        now = datetime.now(timezone.utc).isoformat()

        updates = {
            "status": target_status.value,
            "authorized_at": None,
            "cancelled_at": None,
            "cancellation_reason": None,
        }

        if target_status == ServiceRequestStatus.AUTHORIZED:
            updates["authorized_at"] = now
        elif target_status == ServiceRequestStatus.CANCELLED:
            updates["cancelled_at"] = now
            updates["cancellation_reason"] = cancellation_reason

        connection = self.repository.connection

        def record_audit():
            audit_event(
                event_type=(
                    "service_request_authorized"
                    if target_status == ServiceRequestStatus.AUTHORIZED
                    else "service_request_cancelled"
                ),
                actor_id=actor_id,
                tenant_id=tenant_id,
                action=(
                    "authorize_service_request"
                    if target_status == ServiceRequestStatus.AUTHORIZED
                    else "cancel_service_request"
                ),
                metadata={
                    "service_request_id": request.id,
                    "cancellation_reason": cancellation_reason,
                },
                connection=connection,
            )

        if commit:
            try:
                connection.execute("BEGIN")
                connection.execute(
                    """
                    UPDATE service_requests
                    SET
                        status = ?,
                        authorized_at = COALESCE(authorized_at, ?),
                        cancelled_at = COALESCE(cancelled_at, ?),
                        cancellation_reason = COALESCE(
                            cancellation_reason, ?
                        )
                    WHERE tenant_id = ?
                      AND id = ?
                    """,
                    (
                        updates["status"],
                        updates["authorized_at"],
                        updates["cancelled_at"],
                        updates["cancellation_reason"],
                        tenant_id,
                        request_id,
                    ),
                )
                record_audit()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        else:
            connection.execute(
                """
                UPDATE service_requests
                SET
                    status = ?,
                    authorized_at = COALESCE(authorized_at, ?),
                    cancelled_at = COALESCE(cancelled_at, ?),
                    cancellation_reason = COALESCE(
                        cancellation_reason, ?
                    )
                WHERE tenant_id = ?
                  AND id = ?
                """,
                (
                    updates["status"],
                    updates["authorized_at"],
                    updates["cancelled_at"],
                    updates["cancellation_reason"],
                    tenant_id,
                    request_id,
                ),
            )
            record_audit()

        return self.repository.get(tenant_id, request_id)
