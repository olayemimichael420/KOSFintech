from models.verification import VerificationDecision
from models.verification_outcome import VerificationOutcome


class VerificationDecisionService:
    """Determine the aggregate outcome of independent verifications."""

    REQUIRED_APPROVALS = 2
    REQUIRED_REJECTIONS = 2
    MAX_VERIFIERS = 3

    def __init__(self, verification_repository):
        self.verification_repository = verification_repository

    def evaluate(
        self,
        tenant_id: str,
        service_act_id: int,
    ) -> VerificationOutcome:
        verifications = self.verification_repository.list_by_act(
            tenant_id,
            service_act_id,
        )

        if len(verifications) > self.MAX_VERIFIERS:
            raise ValueError(
                "service act has more than the maximum allowed verifications"
            )

        approvals = sum(
            verification.decision == VerificationDecision.APPROVED
            for verification in verifications
        )

        rejections = sum(
            verification.decision == VerificationDecision.REJECTED
            for verification in verifications
        )

        if approvals >= self.REQUIRED_APPROVALS:
            return VerificationOutcome.APPROVED

        if rejections >= self.REQUIRED_REJECTIONS:
            return VerificationOutcome.REJECTED

        return VerificationOutcome.PENDING
