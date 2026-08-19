from models.authority import (
    Action,
    ActorType,
    AuthorizationRequest,
    Authority,
    AuthorityRole,
    JurisdictionType,
)
from policies.authority_policy import evaluate


def make_request(role, jurisdiction, action):
    authority = Authority(
        actor_id=1,
        actor_type=ActorType.HUMAN,
        role=role,
        jurisdiction_type=jurisdiction,
        jurisdiction_id=(
            "platform"
            if jurisdiction == JurisdictionType.PLATFORM
            else "1"
        ),
        administration_id=(
            None
            if jurisdiction == JurisdictionType.PLATFORM
            else "1"
        ),
    )

    return AuthorizationRequest(
        authority=authority,
        action=action,
        resource_type="administration",
        resource_id="1",
    )


def test_super_admin_cannot_use_administration_jurisdiction():
    request = make_request(
        AuthorityRole.SUPER_ADMIN,
        JurisdictionType.ADMINISTRATION,
        Action.CREATE_ADMINISTRATION,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "super_admin requires platform jurisdiction"


def test_owner_cannot_use_platform_jurisdiction():
    request = make_request(
        AuthorityRole.OWNER,
        JurisdictionType.PLATFORM,
        Action.MANAGE_ADMINISTRATION,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "owner requires administration jurisdiction"


def test_admin1_cannot_use_platform_jurisdiction():
    request = make_request(
        AuthorityRole.ADMIN_1,
        JurisdictionType.PLATFORM,
        Action.MANAGE_USERS,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "administrator requires administration jurisdiction"


def test_admin2_cannot_remove_admin():
    request = make_request(
        AuthorityRole.ADMIN_2,
        JurisdictionType.ADMINISTRATION,
        Action.REMOVE_ADMIN,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for administrator"


def test_owner_can_manage_permissions():
    request = make_request(
        AuthorityRole.OWNER,
        JurisdictionType.ADMINISTRATION,
        Action.MANAGE_PERMISSIONS,
    )

    allowed, reason = evaluate(request)

    assert allowed is True
    assert reason == "owner authorized within administration"


def test_admin1_can_manage_permissions():
    request = make_request(
        AuthorityRole.ADMIN_1,
        JurisdictionType.ADMINISTRATION,
        Action.MANAGE_PERMISSIONS,
    )

    allowed, reason = evaluate(request)

    assert allowed is True
    assert reason == "administrator authorized within administration"


def test_admin2_can_manage_permissions():
    request = make_request(
        AuthorityRole.ADMIN_2,
        JurisdictionType.ADMINISTRATION,
        Action.MANAGE_PERMISSIONS,
    )

    allowed, reason = evaluate(request)

    assert allowed is True
    assert reason == "administrator authorized within administration"


def test_member_is_denied_administrative_action():
    request = make_request(
        AuthorityRole.MEMBER,
        JurisdictionType.ADMINISTRATION,
        Action.MANAGE_USERS,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "member has no administrative authority"


def test_super_admin_can_transfer_super_admin_only_at_platform():
    request = make_request(
        AuthorityRole.SUPER_ADMIN,
        JurisdictionType.PLATFORM,
        Action.TRANSFER_SUPER_ADMIN,
    )

    allowed, reason = evaluate(request)

    assert allowed is True
    assert reason == "super_admin authorized at platform level"


def test_owner_cannot_transfer_super_admin():
    request = make_request(
        AuthorityRole.OWNER,
        JurisdictionType.ADMINISTRATION,
        Action.TRANSFER_SUPER_ADMIN,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for owner"


def test_super_admin_cannot_remove_admin():
    request = make_request(
        AuthorityRole.SUPER_ADMIN,
        JurisdictionType.PLATFORM,
        Action.REMOVE_ADMIN,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for super_admin"


def test_owner_cannot_suspend_administration():
    request = make_request(
        AuthorityRole.OWNER,
        JurisdictionType.ADMINISTRATION,
        Action.SUSPEND_ADMINISTRATION,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for owner"


def test_admin_cannot_suspend_administration():
    request = make_request(
        AuthorityRole.ADMIN_1,
        JurisdictionType.ADMINISTRATION,
        Action.SUSPEND_ADMINISTRATION,
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for administrator"
