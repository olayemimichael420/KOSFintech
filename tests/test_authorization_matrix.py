from models.authority import (
    Action,
    ActorType,
    AuthorizationRequest,
    Authority,
    AuthorityRole,
    JurisdictionType,
)
from policies.authority_policy import authorize


def make_authority(
    role,
    jurisdiction_type,
    jurisdiction_id=None,
):
    return Authority(
        actor_id=1,
        actor_type=ActorType.HUMAN,
        role=role,
        jurisdiction_type=jurisdiction_type,
        jurisdiction_id=jurisdiction_id,
        administration_id=jurisdiction_id,
    )


def request(role, jurisdiction, action):
    return AuthorizationRequest(
        authority=make_authority(role, jurisdiction, "admin-001"),
        action=action,
        resource_type="administration",
        resource_id="admin-001",
    )


def test_super_admin_can_create_administration():
    assert authorize(
        request(
            AuthorityRole.SUPER_ADMIN,
            JurisdictionType.PLATFORM,
            Action.CREATE_ADMINISTRATION,
        )
    )


def test_super_admin_can_suspend_administration():
    assert authorize(
        request(
            AuthorityRole.SUPER_ADMIN,
            JurisdictionType.PLATFORM,
            Action.SUSPEND_ADMINISTRATION,
        )
    )


def test_owner_can_remove_admin():
    assert authorize(
        request(
            AuthorityRole.OWNER,
            JurisdictionType.ADMINISTRATION,
            Action.REMOVE_ADMIN,
        )
    )


def test_admin_cannot_remove_owner():
    assert not authorize(
        request(
            AuthorityRole.ADMIN_1,
            JurisdictionType.ADMINISTRATION,
            Action.REMOVE_OWNER,
        )
    )


def test_admin_cannot_remove_other_admin():
    assert not authorize(
        request(
            AuthorityRole.ADMIN_1,
            JurisdictionType.ADMINISTRATION,
            Action.REMOVE_ADMIN,
        )
    )


def test_owner_cannot_suspend_entire_platform():
    assert not authorize(
        request(
            AuthorityRole.OWNER,
            JurisdictionType.ADMINISTRATION,
            Action.SUSPEND_ADMINISTRATION,
        )
    )


def test_super_admin_requires_platform_jurisdiction():
    assert not authorize(
        request(
            AuthorityRole.SUPER_ADMIN,
            JurisdictionType.ADMINISTRATION,
            Action.SUSPEND_ADMINISTRATION,
        )
    )


def test_member_has_no_administrative_authority():
    assert not authorize(
        request(
            AuthorityRole.MEMBER,
            JurisdictionType.ADMINISTRATION,
            Action.MANAGE_USERS,
        )
    )


def test_unknown_action_is_denied_by_default():
    assert not authorize(
        request(
            AuthorityRole.ADMIN_1,
            JurisdictionType.ADMINISTRATION,
            Action.TERMINATE_ADMINISTRATION,
        )
    )


def test_super_admin_can_transfer_super_admin():
    from models.authority import (
        Action,
        ActorType,
        AuthorizationRequest,
        Authority,
        AuthorityRole,
        JurisdictionType,
    )
    from policies.authority_policy import authorize

    authority = Authority(
        actor_id=1,
        actor_type=ActorType.HUMAN,
        role=AuthorityRole.SUPER_ADMIN,
        jurisdiction_type=JurisdictionType.PLATFORM,
        jurisdiction_id="platform",
    )

    request = AuthorizationRequest(
        authority=authority,
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="2",
    )

    assert authorize(request) is True
