from datetime import datetime, timezone

from audit import audit_event

from models.authority import (
    Action,
    ActorType,
    AuthorizationRequest,
    Authority,
    AuthorityRole,
    JurisdictionType,
)
from models.platform_authority import PlatformAuthorityRole
from policies.authority_policy import authorize
from repositories.platform_authority_repository import (
    PlatformAuthorityRepository,
)


class SuperAdminTransferDecision:
    """Result of a Super Admin transfer attempt."""

    def __init__(self, allowed: bool, reason: str):
        self.allowed = allowed
        self.reason = reason


class SuperAdminTransferService:
    """Safely transfer the platform Super Admin authority."""

    def __init__(self, connection):
        self.connection = connection
        self.repository = PlatformAuthorityRepository(connection)

    def transfer(
        self,
        current_user_id: int,
        target_user_id: int,
    ) -> SuperAdminTransferDecision:
        """Transfer Super Admin authority atomically."""

        if current_user_id == target_user_id:
            return SuperAdminTransferDecision(
                False,
                "cannot transfer super admin role to the current super admin",
            )

        current_authority = self.repository.get_active_by_user(
            current_user_id
        )

        if current_authority is None:
            return SuperAdminTransferDecision(
                False,
                "current user is not the active super admin",
            )

        current_user = self.connection.execute(
            """
            SELECT status
            FROM users
            WHERE id = ?
            """,
            (current_user_id,),
        ).fetchone()

        if current_user is None:
            return SuperAdminTransferDecision(
                False,
                "current user does not exist",
            )

        if current_user["status"] != "active":
            return SuperAdminTransferDecision(
                False,
                "current user is inactive",
            )

        target = self.connection.execute(
            """
            SELECT
                id,
                status
            FROM users
            WHERE id = ?
            """,
            (target_user_id,),
        ).fetchone()

        if target is None:
            return SuperAdminTransferDecision(
                False,
                "target user does not exist",
            )

        if target["status"] != "active":
            return SuperAdminTransferDecision(
                False,
                "target user is inactive",
            )

        authority = Authority(
            actor_id=current_user_id,
            actor_type=ActorType.HUMAN,
            role=AuthorityRole.SUPER_ADMIN,
            jurisdiction_type=JurisdictionType.PLATFORM,
            jurisdiction_id="platform",
        )

        request = AuthorizationRequest(
            authority=authority,
            action=Action.TRANSFER_SUPER_ADMIN,
            resource_type="platform_authority",
            resource_id=str(target_user_id),
        )

        if not authorize(request):
            return SuperAdminTransferDecision(
                False,
                "super admin is not authorized to transfer authority",
            )

        transferred_at = datetime.now(timezone.utc).isoformat()

        try:
            self.connection.execute("BEGIN")

            self.connection.execute(
                """
                UPDATE platform_authorities
                SET
                    status = 'inactive',
                    transferred_at = ?
                WHERE id = ?
                  AND status = 'active'
                """,
                (
                    transferred_at,
                    current_authority.id,
                ),
            )

            self.connection.execute(
                """
                INSERT INTO platform_authorities (
                    user_id,
                    role,
                    status,
                    transferred_at
                )
                VALUES (?, ?, 'active', NULL)
                """,
                (
                    target_user_id,
                    PlatformAuthorityRole.SUPER_ADMIN.value,
                ),
            )

            self.connection.commit()

        except Exception:
            self.connection.rollback()

            return SuperAdminTransferDecision(
                False,
                "super admin transfer failed",
            )

        audit_event(
            event_type="super_admin_transfer",
            actor_id=current_user_id,
            tenant_id="platform",
            action="transfer_super_admin",
            metadata={
                "from_user_id": current_user_id,
                "to_user_id": target_user_id,
            },
        )

        return SuperAdminTransferDecision(
            True,
            "super admin transferred successfully",
        )
