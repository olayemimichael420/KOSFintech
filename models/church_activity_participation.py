from dataclasses import dataclass


@dataclass(frozen=True)
class ChurchActivityParticipation:
    """
    CMOS relationship between a ChurchActivity and a Membership.

    This records that a membership participates in a particular church
    activity within a tenant. It does not establish attendance, learning,
    competence, assessment, score, grade, result, progress, capacity,
    assignment, ecclesiastical authority, authentication, application
    authorization, or permission.
    """
    tenant_id: str
    church_activity_id: int
    membership_id: int
