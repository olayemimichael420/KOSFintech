from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VerificationDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Verification:
    id: Optional[int]
    tenant_id: str
    service_act_id: int
    verifier_user_id: int
    decision: VerificationDecision
    reason: Optional[str] = None
