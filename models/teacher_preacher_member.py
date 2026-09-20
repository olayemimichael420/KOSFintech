from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherPreacherMemberLink:
    """
    CMOS structural relationship between a TeacherPreacher capacity
    and a church Membership within a tenant.

    This entity does not establish ecclesiastical authority,
    ordination, appointment, attendance, participation,
    authentication, application authorization, or permission.
    """

    tenant_id: str
    teacher_preacher_id: int
    membership_id: int
