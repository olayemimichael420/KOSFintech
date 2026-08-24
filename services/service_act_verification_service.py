from audit import audit_event
from models.service_act import ServiceActStatus
from models.verification_outcome import VerificationOutcome


class ServiceActVerificationService:
    """Apply an aggregate verification outcome to a Service Act."""

    def __init__(
        self,
        verification_decision_service,
        service_act_service,
    ):
        self.verification_decision_service = (
            verification_decision_service
        )
        self.service_act_service = service_act_service

    def finalize(
        self,
        tenant_id: str,
        service_act_id: int,
        actor_id: int | None = None,
    ):
        outcome = self.verification_decision_service.evaluate(
            tenant_id,
            service_act_id,
        )

        if outcome == VerificationOutcome.APPROVED:
            updated = self.service_act_service.transition(
                tenant_id,
                service_act_id,
                ServiceActStatus.COMPLETED,
            )

            audit_event(
                event_type="service_act_completed_by_verification",
                actor_id=actor_id,
                tenant_id=tenant_id,
                action="complete_service_act_by_verification",
                metadata={
                    "service_act_id": service_act_id,
                    "verification_outcome": outcome.value,
                },
            )

            return updated

        if outcome == VerificationOutcome.REJECTED:
            updated = self.service_act_service.transition(
                tenant_id,
                service_act_id,
                ServiceActStatus.CANCELLED,
                cancellation_reason=(
                    "Service Act rejected by verification."
                ),
            )

            audit_event(
                event_type="service_act_cancelled_by_verification",
                actor_id=actor_id,
                tenant_id=tenant_id,
                action="cancel_service_act_by_verification",
                metadata={
                    "service_act_id": service_act_id,
                    "verification_outcome": outcome.value,
                },
            )

            return updated

        return self.service_act_service.repository.get(
            tenant_id,
            service_act_id,
        )
