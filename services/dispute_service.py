from datetime import datetime, timezone

from audit import audit_event
from models.dispute import (
    Dispute,
    DisputeInitiatorRole,
    DisputeResolution,
    DisputeStatus,
)


class DisputeService:
    """
    Application service responsible for the Service Act dispute lifecycle.

    Rules:
    - A dispute must belong to the same tenant as its Service Act.
    - Only the provider or recipient of a Service Act may open a dispute.
    - A dispute starts in OPEN status.
    - Only OPEN disputes may enter UNDER_REVIEW.
    - Only UNDER_REVIEW disputes may be RESOLVED or REJECTED.
    - Only OPEN disputes may be WITHDRAWN.
    - Resolution requires a valid resolution and reason.
    - Rejection requires a reason.
    - Withdrawal requires a reason.
    - Every successful consequential operation emits an audit event.
    - Dispute operations do not directly alter Talent Point balances.
    """

    def __init__(self, repository, service_act_repository):
        self.repository = repository
        self.service_act_repository = service_act_repository

    def open_dispute(
        self,
        tenant_id: str,
        service_act_id: int,
        initiator_user_id: int,
        reason: str,
    ) -> Dispute:
        """Open a new dispute against a Service Act."""

        if not reason or not reason.strip():
            raise ValueError("dispute reason is required")

        service_act = self.service_act_repository.get(
            tenant_id,
            service_act_id,
        )

        if service_act is None:
            raise ValueError("service act not found")

        if service_act.tenant_id != tenant_id:
            raise ValueError("tenant mismatch")

        if initiator_user_id == service_act.provider_user_id:
            initiator_role = DisputeInitiatorRole.PROVIDER
        elif initiator_user_id == service_act.recipient_user_id:
            initiator_role = DisputeInitiatorRole.RECIPIENT
        else:
            raise ValueError(
                "only the Service Act provider or recipient may open a dispute"
            )

        dispute = Dispute(
            id=None,
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            initiator_user_id=initiator_user_id,
            initiator_role=initiator_role,
            reason=reason.strip(),
            status=DisputeStatus.OPEN,
            resolution=None,
            resolution_reason=None,
            resolved_by_user_id=None,
            created_at=None,
            resolved_at=None,
        )

        dispute = self.repository.create(dispute)

        audit_event(
            event_type="dispute_opened",
            actor_id=initiator_user_id,
            tenant_id=tenant_id,
            action="open_dispute",
            metadata={
                "dispute_id": dispute.id,
                "service_act_id": dispute.service_act_id,
                "initiator_user_id": dispute.initiator_user_id,
                "initiator_role": dispute.initiator_role.value,
            },
        )

        return dispute

    def move_to_review(
        self,
        tenant_id: str,
        dispute_id: int,
        actor_user_id: int,
    ) -> Dispute:
        """Move an OPEN dispute into UNDER_REVIEW."""

        dispute = self._get_dispute(tenant_id, dispute_id)

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError(
                "only open disputes can be moved to review"
            )

        dispute = self._update_status(
            tenant_id=tenant_id,
            dispute_id=dispute_id,
            status=DisputeStatus.UNDER_REVIEW,
        )

        audit_event(
            event_type="dispute_under_review",
            actor_id=actor_user_id,
            tenant_id=tenant_id,
            action="review_dispute",
            metadata={
                "dispute_id": dispute.id,
                "service_act_id": dispute.service_act_id,
            },
        )

        return dispute

    def resolve(
        self,
        tenant_id: str,
        dispute_id: int,
        resolved_by_user_id: int,
        resolution: DisputeResolution,
        resolution_reason: str,
    ) -> Dispute:
        """Resolve an UNDER_REVIEW dispute."""

        if not isinstance(resolution, DisputeResolution):
            try:
                resolution = DisputeResolution(resolution)
            except (TypeError, ValueError):
                raise ValueError("invalid dispute resolution")

        if not resolution_reason or not resolution_reason.strip():
            raise ValueError("resolution reason is required")

        dispute = self._get_dispute(tenant_id, dispute_id)

        if dispute.status != DisputeStatus.UNDER_REVIEW:
            raise ValueError(
                "only disputes under review can be resolved"
            )

        now = datetime.now(timezone.utc).isoformat()

        self.repository.connection.execute(
            """
            UPDATE disputes
            SET
                status = ?,
                resolution = ?,
                resolution_reason = ?,
                resolved_by_user_id = ?,
                resolved_at = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                DisputeStatus.RESOLVED.value,
                resolution.value,
                resolution_reason.strip(),
                resolved_by_user_id,
                now,
                tenant_id,
                dispute_id,
            ),
        )

        self.repository.connection.commit()

        resolved = self.repository.get(
            tenant_id,
            dispute_id,
        )

        audit_event(
            event_type="dispute_resolved",
            actor_id=resolved_by_user_id,
            tenant_id=tenant_id,
            action="resolve_dispute",
            metadata={
                "dispute_id": resolved.id,
                "service_act_id": resolved.service_act_id,
                "resolution": resolved.resolution.value,
                "resolution_reason": resolved.resolution_reason,
            },
        )

        return resolved

    def reject(
        self,
        tenant_id: str,
        dispute_id: int,
        rejected_by_user_id: int,
        reason: str,
    ) -> Dispute:
        """Reject an UNDER_REVIEW dispute."""

        if not reason or not reason.strip():
            raise ValueError("rejection reason is required")

        dispute = self._get_dispute(tenant_id, dispute_id)

        if dispute.status != DisputeStatus.UNDER_REVIEW:
            raise ValueError(
                "only disputes under review can be rejected"
            )

        now = datetime.now(timezone.utc).isoformat()

        self.repository.connection.execute(
            """
            UPDATE disputes
            SET
                status = ?,
                resolution_reason = ?,
                resolved_by_user_id = ?,
                resolved_at = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                DisputeStatus.REJECTED.value,
                reason.strip(),
                rejected_by_user_id,
                now,
                tenant_id,
                dispute_id,
            ),
        )

        self.repository.connection.commit()

        rejected = self.repository.get(
            tenant_id,
            dispute_id,
        )

        audit_event(
            event_type="dispute_rejected",
            actor_id=rejected_by_user_id,
            tenant_id=tenant_id,
            action="reject_dispute",
            metadata={
                "dispute_id": rejected.id,
                "service_act_id": rejected.service_act_id,
                "reason": rejected.resolution_reason,
            },
        )

        return rejected

    def withdraw(
        self,
        tenant_id: str,
        dispute_id: int,
        actor_user_id: int,
        reason: str,
    ) -> Dispute:
        """Withdraw an OPEN dispute by its initiator."""

        if not reason or not reason.strip():
            raise ValueError("withdrawal reason is required")

        dispute = self._get_dispute(tenant_id, dispute_id)

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError(
                "only open disputes can be withdrawn"
            )

        if actor_user_id != dispute.initiator_user_id:
            raise ValueError(
                "only the dispute initiator may withdraw the dispute"
            )

        self.repository.connection.execute(
            """
            UPDATE disputes
            SET
                status = ?,
                resolution_reason = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                DisputeStatus.WITHDRAWN.value,
                reason.strip(),
                tenant_id,
                dispute_id,
            ),
        )

        self.repository.connection.commit()

        withdrawn = self.repository.get(
            tenant_id,
            dispute_id,
        )

        audit_event(
            event_type="dispute_withdrawn",
            actor_id=actor_user_id,
            tenant_id=tenant_id,
            action="withdraw_dispute",
            metadata={
                "dispute_id": withdrawn.id,
                "service_act_id": withdrawn.service_act_id,
                "reason": withdrawn.resolution_reason,
            },
        )

        return withdrawn

    def _get_dispute(
        self,
        tenant_id: str,
        dispute_id: int,
    ) -> Dispute:
        dispute = self.repository.get(
            tenant_id,
            dispute_id,
        )

        if dispute is None:
            raise ValueError("dispute not found")

        return dispute

    def _update_status(
        self,
        tenant_id: str,
        dispute_id: int,
        status: DisputeStatus,
    ) -> Dispute:
        self.repository.connection.execute(
            """
            UPDATE disputes
            SET status = ?
            WHERE tenant_id = ?
              AND id = ?
            """,
            (
                status.value,
                tenant_id,
                dispute_id,
            ),
        )

        self.repository.connection.commit()

        return self.repository.get(
            tenant_id,
            dispute_id,
        )
