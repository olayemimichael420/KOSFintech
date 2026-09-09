from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JudicialReviewType(str, Enum):
    REVIEW = "review"
    APPEAL = "appeal"


class JudicialReviewStatus(str, Enum):
    PROPOSED = "proposed"


@dataclass(frozen=True)
class JudicialReview:
    """
    J7A judicial review/appeal domain boundary.

    This model records a proposed review or appeal relationship.
    It does not grant appellate authority, determine admissibility,
    impose a stay, reverse or invalidate a decision, reopen a
    proceeding, establish finality, or execute any remedy.
    """

    id: Optional[int]
    tenant_id: str
    proceeding_id: int
    decision_id: int
    originating_judicial_authority_id: int
    jurisdiction_id: int
    review_type: JudicialReviewType
    initiated_by: int
    grounds: str
    status: JudicialReviewStatus = JudicialReviewStatus.PROPOSED
    recorded_at: Optional[str] = None
