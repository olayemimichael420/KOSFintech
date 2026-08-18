from models.authority import (
    Action,
    AuthorizationRequest,
    AuthorityRole,
    JurisdictionType,
)


def evaluate(request: AuthorizationRequest) -> tuple[bool, str]:
    """
    Evaluate an authorization request and return:

        (allowed, reason)

    The policy is deny-by-default.
    """

    authority = request.authority

    # ---------------------------------------------------------
    # SUPER ADMIN
    # ---------------------------------------------------------
    if authority.role == AuthorityRole.SUPER_ADMIN:
        if authority.jurisdiction_type != JurisdictionType.PLATFORM:
            return False, "super_admin requires platform jurisdiction"

        if request.action in {
            Action.CREATE_ADMINISTRATION,
            Action.SUSPEND_ADMINISTRATION,
            Action.TRANSFER_SUPER_ADMIN,
        }:
            return True, "super_admin authorized at platform level"

        return False, "action is not permitted for super_admin"

    # ---------------------------------------------------------
    # OWNER
    # ---------------------------------------------------------
    if authority.role == AuthorityRole.OWNER:
        if authority.jurisdiction_type != JurisdictionType.ADMINISTRATION:
            return False, "owner requires administration jurisdiction"

        if request.action in {
            Action.REMOVE_ADMIN,
            Action.APPOINT_ADMIN,
            Action.MANAGE_ADMINISTRATION,
            Action.MANAGE_USERS,
            Action.MANAGE_ROLES,
            Action.MANAGE_PERMISSIONS,
        }:
            return True, "owner authorized within administration"

        return False, "action is not permitted for owner"

    # ---------------------------------------------------------
    # ADMIN 1 / ADMIN 2
    # ---------------------------------------------------------
    if authority.role in {
        AuthorityRole.ADMIN_1,
        AuthorityRole.ADMIN_2,
    }:
        if authority.jurisdiction_type != JurisdictionType.ADMINISTRATION:
            return False, "administrator requires administration jurisdiction"

        if request.action in {
            Action.MANAGE_USERS,
            Action.MANAGE_ROLES,
            Action.MANAGE_PERMISSIONS,
        }:
            return True, "administrator authorized within administration"

        return False, "action is not permitted for administrator"

    # ---------------------------------------------------------
    # MEMBER
    # ---------------------------------------------------------
    if authority.role == AuthorityRole.MEMBER:
        return False, "member has no administrative authority"

    # ---------------------------------------------------------
    # FAIL CLOSED
    # ---------------------------------------------------------
    return False, "authorization denied by default"


def authorize(request: AuthorizationRequest) -> bool:
    """
    Backward-compatible boolean authorization interface.
    """
    allowed, _ = evaluate(request)
    return allowed
