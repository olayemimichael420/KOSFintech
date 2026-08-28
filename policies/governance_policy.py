from enum import Enum


class GovernanceAction(str, Enum):
    CREATE_PROPOSAL = "create_proposal"
    OPEN_PROPOSAL = "open_proposal"
    CAST_VOTE = "cast_vote"
    CLOSE_PROPOSAL = "close_proposal"
    CANCEL_PROPOSAL = "cancel_proposal"


def evaluate(
    *,
    action: GovernanceAction,
    is_active_user: bool,
    same_tenant: bool,
) -> tuple[bool, str]:
    """
    Pure governance eligibility policy.

    Constitutional role assignments are intentionally NOT inferred here.
    Governance authority remains deny-by-default until explicitly defined.
    """
    if not is_active_user:
        return False, "governance requires an active user"

    if not same_tenant:
        return False, "governance tenant mismatch"

    return False, "governance action not yet constitutionally authorized"
