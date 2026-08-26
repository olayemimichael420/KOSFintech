from audit import audit_event
from models.service_act import ServiceActStatus
from models.reputation import ReputationEvent
from services.reputation_policy import ReputationPolicy


class ReputationService:
    """Application service for Service Act reputation submissions."""

    MIN_SCORE = 1
    MAX_SCORE = 5

    def __init__(self, repository, service_act_repository):
        self.repository = repository
        self.service_act_repository = service_act_repository

    def submit(
        self,
        tenant_id: str,
        service_act_id: int,
        reviewer_user_id: int,
        score: int,
        comment: str | None = None,
    ) -> ReputationEvent:

        # 1. Validate score through the domain policy.
        ReputationPolicy.validate_score(score)

        # 2. Load Service Act within tenant boundary.
        service_act = self.service_act_repository.get(
            tenant_id,
            service_act_id,
        )

        if service_act is None:
            raise ValueError("service act not found")

        # 3. Reputation is only valid after successful completion.
        if service_act.status != ServiceActStatus.COMPLETED:
            raise ValueError(
                "reputation can only be submitted for completed Service Acts"
            )

        # 4. Only the recipient may review the provider.
        if reviewer_user_id != service_act.recipient_user_id:
            raise ValueError(
                "only the Service Act recipient may submit reputation"
            )

        # 5. Prevent duplicate reputation for the same Service Act.
        if self.repository.exists_for_service_act(
            tenant_id,
            service_act_id,
        ):
            raise ValueError(
                "reputation already exists for service act"
            )

        # 6. Create immutable reputation event.
        event = ReputationEvent(
            id=None,
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            subject_user_id=service_act.provider_user_id,
            reviewer_user_id=reviewer_user_id,
            score=score,
            comment=comment,
            created_at=None,
        )

        connection = self.repository.connection

        try:
            connection.execute("BEGIN")

            event = self.repository.create(event)

            # ---------------------------------------------------------
            # 7. Emit audit event using the SAME transaction
            # ---------------------------------------------------------
            audit_event(
                event_type="reputation_submitted",
                actor_id=reviewer_user_id,
                tenant_id=tenant_id,
                action="submit_service_act_reputation",
                metadata={
                    "reputation_event_id": event.id,
                    "service_act_id": event.service_act_id,
                    "subject_user_id": event.subject_user_id,
                    "reviewer_user_id": event.reviewer_user_id,
                    "score": event.score,
                },
                connection=connection,
            )

            connection.commit()

            # ---------------------------------------------------------
            # 8. Return committed reputation event
            # ---------------------------------------------------------
            return event

        except Exception:
            connection.rollback()
            raise
