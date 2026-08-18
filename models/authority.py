from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActorType(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"


class AuthorityRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    ADMIN_1 = "admin1"
    ADMIN_2 = "admin2"
    MEMBER = "member"


class JurisdictionType(str, Enum):
    PLATFORM = "platform"
    ADMINISTRATION = "administration"
    RESOURCE = "resource"


class Action(str, Enum):
    CREATE_ADMINISTRATION = "create_administration"
    SUSPEND_ADMINISTRATION = "suspend_administration"
    TRANSFER_SUPER_ADMIN = "transfer_super_admin"
    TERMINATE_ADMINISTRATION = "terminate_administration"

    MANAGE_ADMINISTRATION = "manage_administration"

    APPOINT_ADMIN = "appoint_admin"
    REMOVE_ADMIN = "remove_admin"

    REMOVE_OWNER = "remove_owner"

    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"

    EXECUTE_AUTONOMOUS_ACTION = "execute_autonomous_action"


@dataclass(frozen=True)
class Authority:
    actor_id: int
    actor_type: ActorType
    role: AuthorityRole
    jurisdiction_type: JurisdictionType
    jurisdiction_id: Optional[str] = None
    administration_id: Optional[str] = None


@dataclass(frozen=True)
class AuthorizationRequest:
    authority: Authority
    action: Action
    resource_type: str
    resource_id: Optional[str] = None


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
