from dataclasses import dataclass


@dataclass(frozen=True)
class TeachingSessionMemberLink:
    """
    CMOS structural relationship between a TeachingSession
    and a church Membership within a tenant.

    This entity does not establish attendance, participation,
    learning evidence, assessment, result, ecclesiastical authority,
    authentication, application authorization, or permission.
    """

    tenant_id: str
    teaching_session_id: int
    membership_id: int
