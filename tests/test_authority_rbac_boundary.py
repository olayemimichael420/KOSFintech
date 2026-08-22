import sqlite3

from models.authority import (
    Action,
    ActorType,
    AuthorizationRequest,
    Authority,
    AuthorityRole,
    JurisdictionType,
)
from policies.authority_policy import evaluate


def make_authority(role):
    return Authority(
        actor_id=1,
        actor_type=ActorType.HUMAN,
        role=role,
        jurisdiction_type=JurisdictionType.ADMINISTRATION,
        jurisdiction_id="1",
        administration_id="1",
    )


def test_application_role_does_not_become_authority():
    """
    Application roles such as teacher must not grant
    governance authority by themselves.
    """
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    connection.execute(
        """
        INSERT INTO roles (
            tenant_id,
            name,
            description,
            status
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "school-001",
            "teacher",
            "Teaching staff",
            "active",
        ),
    )

    row = connection.execute(
        "SELECT name FROM roles WHERE name = ?",
        ("teacher",),
    ).fetchone()

    assert row[0] == "teacher"

    # A database application role does not itself create
    # an Authority object or administrative privilege.
    request = AuthorizationRequest(
        authority=make_authority(AuthorityRole.MEMBER),
        action=Action.MANAGE_USERS,
        resource_type="administration",
        resource_id="1",
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "member has no administrative authority"

    connection.close()


def test_owner_authority_does_not_imply_teacher_application_role():
    """
    Governance authority and application roles remain independent.
    """
    request = AuthorizationRequest(
        authority=make_authority(AuthorityRole.OWNER),
        action=Action.MANAGE_USERS,
        resource_type="administration",
        resource_id="1",
    )

    allowed, reason = evaluate(request)

    assert allowed is True
    assert reason == "owner authorized within administration"


def test_member_authority_cannot_manage_permissions():
    """
    Having a valid identity/member status does not grant
    permission-management authority.
    """
    request = AuthorizationRequest(
        authority=make_authority(AuthorityRole.MEMBER),
        action=Action.MANAGE_PERMISSIONS,
        resource_type="permission",
        resource_id="1",
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "member has no administrative authority"


def test_authority_action_is_not_an_rbac_permission():
    """
    Governance actions remain separate from application permissions.
    """
    request = AuthorizationRequest(
        authority=make_authority(AuthorityRole.ADMIN_1),
        action=Action.TRANSFER_SUPER_ADMIN,
        resource_type="platform_authority",
        resource_id="2",
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "action is not permitted for administrator"

def test_ai_agent_cannot_transfer_super_admin():
    authority = Authority(
        actor_id=1,
        actor_type=ActorType.AI_AGENT,
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

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "ai agent cannot exercise human governance authority"


def test_system_cannot_transfer_super_admin():
    authority = Authority(
        actor_id=1,
        actor_type=ActorType.SYSTEM,
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

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "system cannot exercise human governance authority"


def test_ai_agent_autonomous_action_is_denied_by_default():
    authority = Authority(
        actor_id=1,
        actor_type=ActorType.AI_AGENT,
        role=AuthorityRole.MEMBER,
        jurisdiction_type=JurisdictionType.RESOURCE,
        jurisdiction_id="resource-1",
    )

    request = AuthorizationRequest(
        authority=authority,
        action=Action.EXECUTE_AUTONOMOUS_ACTION,
        resource_type="resource",
        resource_id="resource-1",
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "authorization denied by default"


def test_system_autonomous_action_is_denied_by_default():
    authority = Authority(
        actor_id=1,
        actor_type=ActorType.SYSTEM,
        role=AuthorityRole.MEMBER,
        jurisdiction_type=JurisdictionType.RESOURCE,
        jurisdiction_id="resource-1",
    )

    request = AuthorizationRequest(
        authority=authority,
        action=Action.EXECUTE_AUTONOMOUS_ACTION,
        resource_type="resource",
        resource_id="resource-1",
    )

    allowed, reason = evaluate(request)

    assert allowed is False
    assert reason == "authorization denied by default"
