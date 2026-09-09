from dataclasses import dataclass


@dataclass(frozen=True)
class JudicialReviewExecutionDecision:
    allowed: bool
    reason: str


class JudicialReviewExecutionBoundary:
    """
    J7D fail-closed boundary.

    This service does not grant, infer, or establish judicial
    review/appeal authority. Until the constitutional authority,
    jurisdiction, procedure, effect, and finality of judicial
    review/appeal are established, execution is denied.
    """

    def __init__(self, connection):
        self.connection = connection

    def authorize_execution(
        self,
        *,
        review_id: int,
    ) -> JudicialReviewExecutionDecision:
        return JudicialReviewExecutionDecision(
            allowed=False,
            reason=(
                "judicial review/appeal execution authority "
                "is not established"
            ),
        )
