from audit import audit_event
from models.authority import Action
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermissionLink
from models.user_role import UserRoleLink
from repositories.permission_repository import PermissionRepository
from repositories.role_permission_repository import RolePermissionRepository
from repositories.role_repository import RoleRepository
from repositories.user_role_repository import UserRoleRepository
from services.authorization_service import AuthorizationService


class RBACProvisioningService:
    """
    Administration-authorized application RBAC provisioning boundary.

    Governance authorization determines whether an administration
    authority may manage application RBAC. This service does not create
    or infer governance authority and does not decide which application
    roles or permissions should exist.
    """

    def __init__(self, connection, authorization_service=None):
        self.connection = connection
        self.authorization_service = (
            authorization_service or AuthorizationService(connection)
        )
        self.role_repository = RoleRepository(connection)
        self.permission_repository = PermissionRepository(connection)
        self.user_role_repository = UserRoleRepository(connection)
        self.role_permission_repository = RolePermissionRepository(connection)

    def _tenant_for_actor(self, user_id: int) -> str:
        row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None or row["status"] != "active":
            raise PermissionError(
                "authenticated user is inactive or not found"
            )

        return row["tenant_id"]

    def _authorize(
        self,
        user_id: int,
        administration_id: int,
        action: Action,
    ) -> str:
        tenant_id = self._tenant_for_actor(user_id)

        decision = self.authorization_service.authorize_decision(
            user_id=user_id,
            administration_id=administration_id,
            action=action,
            resource_type="administration",
            resource_id=str(administration_id),
        )

        if not decision.allowed:
            raise PermissionError(decision.reason)

        return tenant_id

    def _require_target_user(
        self,
        tenant_id: str,
        user_id: int,
    ) -> None:
        row = self.connection.execute(
            """
            SELECT id, status
            FROM users
            WHERE id = ?
              AND tenant_id = ?
            """,
            (user_id, tenant_id),
        ).fetchone()

        if row is None:
            raise ValueError("target user not found")

        if row["status"] != "active":
            raise ValueError("target user is inactive")

    def create_role(
        self,
        user_id: int,
        administration_id: int,
        role: Role,
    ) -> Role:
        tenant_id = self._authorize(
            user_id,
            administration_id,
            Action.MANAGE_ROLES,
        )

        if role.tenant_id != tenant_id:
            raise ValueError("role tenant mismatch")

        if not role.name.strip():
            raise ValueError("role name is required")

        created = self.role_repository.create(role)

        audit_event(
            event_type="rbac_role_created",
            actor_id=user_id,
            tenant_id=tenant_id,
            action="create_role",
            metadata={
                "administration_id": administration_id,
                "role_id": created.id,
                "role_name": created.name,
            },
            connection=self.connection,
        )

        return created

    def create_permission(
        self,
        user_id: int,
        administration_id: int,
        permission: Permission,
    ) -> Permission:
        tenant_id = self._authorize(
            user_id,
            administration_id,
            Action.MANAGE_PERMISSIONS,
        )

        if permission.tenant_id != tenant_id:
            raise ValueError("permission tenant mismatch")

        if not permission.name.strip():
            raise ValueError("permission name is required")

        created = self.permission_repository.create(permission)

        audit_event(
            event_type="rbac_permission_created",
            actor_id=user_id,
            tenant_id=tenant_id,
            action="create_permission",
            metadata={
                "administration_id": administration_id,
                "permission_id": created.id,
                "permission_name": created.name,
            },
            connection=self.connection,
        )

        return created

    def assign_role_to_user(
        self,
        user_id: int,
        administration_id: int,
        target_user_id: int,
        role_id: int,
    ) -> UserRoleLink:
        tenant_id = self._authorize(
            user_id,
            administration_id,
            Action.MANAGE_USERS,
        )

        self._require_target_user(tenant_id, target_user_id)

        role = self.role_repository.get(tenant_id, role_id)

        if role is None:
            raise ValueError("role not found")

        if role.status != "active":
            raise ValueError("role is inactive")

        link = UserRoleLink(
            tenant_id=tenant_id,
            user_id=target_user_id,
            role_id=role_id,
        )

        created = self.user_role_repository.create(link)

        audit_event(
            event_type="rbac_role_assigned",
            actor_id=user_id,
            tenant_id=tenant_id,
            action="assign_role_to_user",
            metadata={
                "administration_id": administration_id,
                "target_user_id": target_user_id,
                "role_id": role_id,
            },
            connection=self.connection,
        )

        return created

    def grant_permission_to_role(
        self,
        user_id: int,
        administration_id: int,
        role_id: int,
        permission_id: int,
    ) -> RolePermissionLink:
        tenant_id = self._authorize(
            user_id,
            administration_id,
            Action.MANAGE_PERMISSIONS,
        )

        role = self.role_repository.get(tenant_id, role_id)

        if role is None:
            raise ValueError("role not found")

        if role.status != "active":
            raise ValueError("role is inactive")

        permission = self.permission_repository.get(
            tenant_id,
            permission_id,
        )

        if permission is None:
            raise ValueError("permission not found")

        if permission.status != "active":
            raise ValueError("permission is inactive")

        link = RolePermissionLink(
            tenant_id=tenant_id,
            role_id=role_id,
            permission_id=permission_id,
        )

        created = self.role_permission_repository.create(link)

        audit_event(
            event_type="rbac_permission_granted",
            actor_id=user_id,
            tenant_id=tenant_id,
            action="grant_permission_to_role",
            metadata={
                "administration_id": administration_id,
                "role_id": role_id,
                "permission_id": permission_id,
            },
            connection=self.connection,
        )

        return created
