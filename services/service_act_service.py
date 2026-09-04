from datetime import datetime, timezone

from models.service_act import ServiceActStatus
from services.permission_resolution_service import PermissionResolutionService


class ServiceActService:
    """Application service responsible for Service Act lifecycle transitions."""

    WRITE_PERMISSION = "service_act.write"

    _TRANSITIONS = {
        ServiceActStatus.CREATED: {
            ServiceActStatus.ACCEPTED,
            ServiceActStatus.CANCELLED,
        },
        ServiceActStatus.ACCEPTED: {
            ServiceActStatus.IN_PROGRESS,
            ServiceActStatus.CANCELLED,
        },
        ServiceActStatus.IN_PROGRESS: {
            ServiceActStatus.SUBMITTED,
            ServiceActStatus.CANCELLED,
        },
        ServiceActStatus.SUBMITTED: {
            ServiceActStatus.COMPLETED,
            ServiceActStatus.CANCELLED,
        },
        ServiceActStatus.COMPLETED: set(),
        ServiceActStatus.CANCELLED: set(),
    }

    def __init__(
        self,
        repository,
        permission_service: PermissionResolutionService,
    ):
        self.repository = repository
        self.permission_service = permission_service

    def transition(
        self,
        tenant_id: str,
        act_id: int,
        target_status: ServiceActStatus,
        cancellation_reason: str | None = None,
        commit: bool = True,
        actor_id: int | None = None,
    ):
        """
        Execute an externally authorized Service Act lifecycle command.

        Actor eligibility is transition-specific:
        - ACCEPTED: recipient
        - IN_PROGRESS: provider
        - SUBMITTED: provider
        - CANCELLED: provider or recipient

        COMPLETED and verification-driven CANCELLED transitions are
        controlled internally by the verification workflow.
        """
        if actor_id is None:
            raise PermissionError("service act actor is required")

        if not self.permission_service.has_permission(
            user_id=actor_id,
            permission_name=self.WRITE_PERMISSION,
            tenant_id=tenant_id,
        ):
            raise PermissionError("service act permission denied")

        act = self.repository.get(tenant_id, act_id)

        if act is None:
            raise ValueError("service act not found")

        if not self._actor_can_perform_transition(
            act,
            target_status,
            actor_id,
        ):
            raise PermissionError(
                "service act actor is not authorized for this transition"
            )

        return self._apply_transition(
            tenant_id=tenant_id,
            act_id=act_id,
            target_status=target_status,
            cancellation_reason=cancellation_reason,
            commit=commit,
        )

    def _transition_internal(
        self,
        tenant_id: str,
        act_id: int,
        target_status: ServiceActStatus,
        cancellation_reason: str | None = None,
        commit: bool = True,
    ):
        """
        Apply a workflow-controlled Service Act transition.

        This path is intentionally not exposed as an ordinary authorization
        command. It is used by controlled internal application workflows,
        such as verification finalization.
        """
        return self._apply_transition(
            tenant_id=tenant_id,
            act_id=act_id,
            target_status=target_status,
            cancellation_reason=cancellation_reason,
            commit=commit,
        )

    def _actor_can_perform_transition(
        self,
        act,
        target_status: ServiceActStatus,
        actor_id: int,
    ) -> bool:
        if target_status == ServiceActStatus.ACCEPTED:
            return actor_id == act.recipient_user_id

        if target_status in (
            ServiceActStatus.IN_PROGRESS,
            ServiceActStatus.SUBMITTED,
        ):
            return actor_id == act.provider_user_id

        if target_status == ServiceActStatus.CANCELLED:
            return actor_id in (
                act.provider_user_id,
                act.recipient_user_id,
            )

        return False

    def _apply_transition(
        self,
        tenant_id: str,
        act_id: int,
        target_status: ServiceActStatus,
        cancellation_reason: str | None = None,
        commit: bool = True,
    ):
        act = self.repository.get(tenant_id, act_id)

        if act is None:
            raise ValueError("service act not found")

        if target_status not in self._TRANSITIONS[act.status]:
            raise ValueError(
                f"invalid service act transition: "
                f"{act.status.value} -> {target_status.value}"
            )

        if (
            target_status == ServiceActStatus.CANCELLED
            and not cancellation_reason
        ):
            raise ValueError(
                "cancellation reason is required"
            )

        now = datetime.now(timezone.utc).isoformat()

        updates = {
            "status": target_status.value,
        }

        if target_status == ServiceActStatus.ACCEPTED:
            updates["accepted_at"] = now

        elif target_status == ServiceActStatus.IN_PROGRESS:
            updates["started_at"] = now

        elif target_status == ServiceActStatus.SUBMITTED:
            updates["submitted_at"] = now

        elif target_status == ServiceActStatus.COMPLETED:
            updates["completed_at"] = now

        elif target_status == ServiceActStatus.CANCELLED:
            updates["cancelled_at"] = now
            updates["cancellation_reason"] = cancellation_reason

        self.repository.connection.execute(
            """
            UPDATE service_acts
            SET
                status = ?,
                accepted_at = COALESCE(accepted_at, ?),
                started_at = COALESCE(started_at, ?),
                submitted_at = COALESCE(submitted_at, ?),
                completed_at = COALESCE(completed_at, ?),
                cancelled_at = COALESCE(cancelled_at, ?),
                cancellation_reason = COALESCE(
                    cancellation_reason,
                    ?
                )
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                updates["status"],
                updates.get("accepted_at"),
                updates.get("started_at"),
                updates.get("submitted_at"),
                updates.get("completed_at"),
                updates.get("cancelled_at"),
                updates.get("cancellation_reason"),
                tenant_id,
                act_id,
            ),
        )

        if commit:
            self.repository.connection.commit()

        return self.repository.get(tenant_id, act_id)
