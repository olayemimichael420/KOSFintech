from models.verification import VerificationDecision


class VerificationWorkflowService:
    """
    Orchestrate verification submission and Service Act finalization.

    VerificationService records an individual verifier decision.
    VerificationDecisionService determines the aggregate outcome.
    ServiceActVerificationService applies that outcome to the Service Act.
    """

    def __init__(
        self,
        verification_service,
        service_act_verification_service,
    ):
        self.verification_service = verification_service
        self.service_act_verification_service = (
            service_act_verification_service
        )

    def verify(
        self,
        tenant_id: str,
        service_act_id: int,
        verifier_user_id: int,
        decision: VerificationDecision,
        reason: str | None = None,
        actor_id: int | None = None,
    ):
        """
        Record a verification and immediately attempt finalization.

        If the aggregate result is still pending, the Service Act remains
        submitted.

        Returns:
            (verification, service_act)
        """

        verification = self.verification_service.verify(
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            verifier_user_id=verifier_user_id,
            decision=decision,
            reason=reason,
        )

        service_act = self.service_act_verification_service.finalize(
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            actor_id=(
                actor_id
                if actor_id is not None
                else verifier_user_id
            ),
        )

        return verification, service_act
