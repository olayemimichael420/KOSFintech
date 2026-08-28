from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GovernanceVoteChoice(str, Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class GovernanceVote:
    id: Optional[int]
    tenant_id: str
    proposal_id: int
    voter_user_id: int
    choice: GovernanceVoteChoice
    created_at: Optional[str] = None
