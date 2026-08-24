from audit import audit_event
from models.service_act import ServiceActStatus
from models.verification import Verification, VerificationDecision


class VerificationService:
    """Application service responsible for submitting independent verifications."""

    MAX_VERIFIERS = 3

    def __init__(self, repository, service_act_repository):
        self.repository = repository
        self.service_act_repository = service_act_repository

    def verify(
        self,
        tenant_id: str,
        service_act_id: int,
        verifier_user_id: int,
        decision: VerificationDecision,
        reason: str | None = None,
    ) -> Verification:

        act = self.service_act_repository.get(
            tenant_id,
            service_act_id,
        )

        if act is None:
            raise ValueError("service act not found")

        if act.status != ServiceActStatus.SUBMITTED:
            raise ValueError(
                "service act must be submitted before verification"
            )

        if verifier_user_id in (
            act.provider_user_id,
            act.recipient_user_id,
        ):
            raise ValueError(
                "provider or recipient cannot verify their own service act"
            )

        existing = self.repository.list_by_act(
            tenant_id,
            service_act_id,
        )

        if len(existing) >= self.MAX_VERIFIERS:
            raise ValueError(
                "maximum of 3 verifiers allowed for a service act"
            )

        if any(
            verification.verifier_user_id == verifier_user_id
            for verification in existing
        ):
            raise ValueError(
                "verifier has already verified this service act"
            )

        if (
            decision == VerificationDecision.REJECTED
            and not reason
        ):
            raise ValueError(
                "rejection reason is required"
            )

        verification = Verification(
            id=None,
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            verifier_user_id=verifier_user_id,
            decision=decision,
            reason=reason,
        )

        created = self.repository.create(verification)

        audit_event(
            event_type="verification_submitted",
            actor_id=verifier_user_id,
            tenant_id=tenant_id,
            action="submit_verification",
            metadata={
                "verification_id": created.id,
                "service_act_id": service_act_id,
                "decision": created.decision.value,
                "reason": created.reason,
            },
        )

        return created

