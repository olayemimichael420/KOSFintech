from datetime import datetime, timezone

from models.service_act import ServiceActStatus


class ServiceActService:
    """Application service responsible for Service Act lifecycle transitions."""

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

    def __init__(self, repository):
        self.repository = repository

    def transition(
        self,
        tenant_id: str,
        act_id: int,
        target_status: ServiceActStatus,
        cancellation_reason: str | None = None,
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

        self.repository.connection.commit()

        return self.repository.get(tenant_id, act_id)
