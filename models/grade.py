from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Grade:
    """
    CMOS grade classification for an assessment score range.

    This entity defines an interpretive score classification.
    It does not establish a score, result, progress, competence,
    qualification, attendance, learning evidence, ecclesiastical
    authority, spiritual standing, divine standing, or application
    authorization.
    """

    id: Optional[int]
    tenant_id: str
    name: str
    description: Optional[str] = None
    minimum_score: int = 0
    maximum_score: int = 0
    status: str = "active"
