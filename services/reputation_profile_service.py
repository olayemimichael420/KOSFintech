from models.reputation_profile import ReputationProfile


class ReputationProfileService:
    """Build derived reputation profiles from reputation events."""

    def __init__(self, repository):
        self.repository = repository

    def get_profile(
        self,
        tenant_id: str,
        user_id: int,
    ) -> ReputationProfile:
        """Return the current derived reputation profile for a user."""

        summary = self.repository.get_score_summary(
            tenant_id,
            user_id,
        )

        return ReputationProfile(
            tenant_id=tenant_id,
            user_id=user_id,
            average_score=summary["average_score"],
            total_reviews=summary["total_reviews"],
            score_5_count=summary["score_5_count"],
            score_4_count=summary["score_4_count"],
            score_3_count=summary["score_3_count"],
            score_2_count=summary["score_2_count"],
            score_1_count=summary["score_1_count"],
        )
