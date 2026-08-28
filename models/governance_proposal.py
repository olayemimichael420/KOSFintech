from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GovernanceProposalStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class GovernanceProposal:
    id: Optional[int]
    tenant_id: str
    proposer_user_id: int
    title: str
    description: str
    status: GovernanceProposalStatus = GovernanceProposalStatus.DRAFT
    created_at: Optional[str] = None
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None
