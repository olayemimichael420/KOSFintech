from dataclasses import dataclass


@dataclass(frozen=True)
class ReputationProfile:
    """Derived reputation summary for a user within a tenant."""

    tenant_id: str
    user_id: int
    average_score: float
    total_reviews: int
    score_5_count: int
    score_4_count: int
    score_3_count: int
    score_2_count: int
    score_1_count: int
