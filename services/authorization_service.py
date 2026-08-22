from typing import Optional

from models.authority import (
    Action,
    ActorType,
    AuthorizationDecision,
    AuthorizationRequest,
    Authority,
    AuthorityRole,
    JurisdictionType,
)
from policies.authority_policy import evaluate
from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)
from services.permission_resolution_service import PermissionResolutionService


class AuthorizationService:
    """
    Database-backed authorization service.

    The repository establishes which role the user actually holds
    within an administration.

    The authority policy then determines whether that role may
    perform the requested action.

    The service exposes both:
        - authorize()          -> bool
        - authorize_decision() -> AuthorizationDecision
    """

    def __init__(self, connection):
        self.connection = connection
        self.repository = AdministrationAuthorityRepository(connection)
        self.permission_service = PermissionResolutionService(connection)

    def has_permission(
        self,
        user_id: int,
        permission_name: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Check application RBAC permission independently of governance authority."""
        return self.permission_service.has_permission(
            user_id=user_id,
            permission_name=permission_name,
            tenant_id=tenant_id,
        )

    def authorize(
        self,
        user_id: int,
        administration_id: int,
        action: Action,
        resource_type: str = "administration",
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Backward-compatible boolean authorization interface.
        """
        decision = self.authorize_decision(
            user_id=user_id,
            administration_id=administration_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        return decision.allowed

    def authorize_decision(
        self,
        user_id: int,
        administration_id: int,
        action: Action,
        resource_type: str = "administration",
        resource_id: Optional[str] = None,
    ) -> AuthorizationDecision:
        """
        Evaluate authorization and return both the decision
        and an explanatory reason.
        """

        user_row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None:
            return AuthorizationDecision(
                allowed=False,
                reason="authenticated user not found",
            )

        if user_row["status"] != "active":
            return AuthorizationDecision(
                allowed=False,
                reason="authenticated user is inactive",
            )

        tenant_id = user_row["tenant_id"]

        administration_row = self.connection.execute(
            """
            SELECT tenant_id
            FROM administrations
            WHERE id = ?
            """,
            (administration_id,),
        ).fetchone()

        if administration_row is None:
            return AuthorizationDecision(
                allowed=False,
                reason="administration not found",
            )

        if administration_row["tenant_id"] != tenant_id:
            return AuthorizationDecision(
                allowed=False,
                reason="administration tenant mismatch",
            )

        assignment = (
            self.repository.get_active_by_user_and_administration(
                tenant_id=tenant_id,
                user_id=user_id,
                administration_id=administration_id,
            )
        )

        if assignment is None:
            return AuthorizationDecision(
                allowed=False,
                reason="no active authority assignment",
            )

        try:
            role = AuthorityRole(assignment.role.value)
        except ValueError:
            return AuthorizationDecision(
                allowed=False,
                reason="invalid authority role",
            )

        authority = Authority(
            actor_id=user_id,
            actor_type=ActorType.HUMAN,
            role=role,
            jurisdiction_type=JurisdictionType.ADMINISTRATION,
            jurisdiction_id=str(administration_id),
            administration_id=str(administration_id),
        )

        request = AuthorizationRequest(
            authority=authority,
            action=action,
            resource_type=resource_type,
            resource_id=(
                resource_id
                if resource_id is not None
                else str(administration_id)
            ),
        )

        allowed, reason = evaluate(request)

        return AuthorizationDecision(
            allowed=allowed,
            reason=reason,
        )


    def authorize_context(
        self,
        context,
        administration_id: int,
        action: Action,
        resource_type: str = "administration",
        resource_id: Optional[str] = None,
    ) -> AuthorizationDecision:
        """
        Authorize an already-resolved KOSFintech security context.

        The context must come from AuthorizationContextService.
        Application roles are never treated as governance authority.
        """

        if context.user_id is None:
            return AuthorizationDecision(
                allowed=False,
                reason="missing authenticated user",
            )

        # A resolved context is a snapshot. Revalidate the authenticated
        # user's current status before granting any governance authority.
        user_row = self.connection.execute(
            """
            SELECT status
            FROM users
            WHERE id = ?
            """,
            (context.user_id,),
        ).fetchone()

        if user_row is None:
            return AuthorizationDecision(
                allowed=False,
                reason="authenticated user not found",
            )

        if user_row["status"] != "active":
            return AuthorizationDecision(
                allowed=False,
                reason="authenticated user is inactive",
            )

        # Platform authority is distinct from administration authority.
        # A resolved context is a snapshot, so platform authority must be
        # revalidated against the current database state before authorization.
        if context.is_super_admin:
            current_platform_authority = (
                self.connection.execute(
                    """
                    SELECT id
                    FROM platform_authorities
                    WHERE user_id = ?
                      AND role = 'super_admin'
                      AND status = 'active'
                    LIMIT 1
                    """,
                    (context.user_id,),
                ).fetchone()
            )

            if current_platform_authority is None:
                return AuthorizationDecision(
                    allowed=False,
                    reason="no active platform super admin authority",
                )
            authority = Authority(
                actor_id=context.user_id,
                actor_type=ActorType.HUMAN,
                role=AuthorityRole.SUPER_ADMIN,
                jurisdiction_type=JurisdictionType.PLATFORM,
                jurisdiction_id="platform",
                administration_id=None,
            )

            request = AuthorizationRequest(
                authority=authority,
                action=action,
                resource_type=resource_type,
                resource_id=(
                    resource_id
                    if resource_id is not None
                    else str(administration_id)
                ),
            )

            allowed, reason = evaluate(request)

            return AuthorizationDecision(
                allowed=allowed,
                reason=reason,
            )

        # Administration authority must belong to the requested
        # administration. Never allow a context from one administration
        # to authorize an action against another.
        if context.administration_id != administration_id:
            return AuthorizationDecision(
                allowed=False,
                reason="administration context mismatch",
            )

        # The resolved context is a snapshot. Revalidate the current
        # administration authority before granting governance access.
        current_authority = self.connection.execute(
            """
            SELECT aa.role
            FROM administration_authorities AS aa
            JOIN users AS u
              ON u.id = aa.user_id
            WHERE aa.tenant_id = u.tenant_id
              AND aa.administration_id = ?
              AND aa.user_id = ?
              AND aa.status = 'active'
              AND u.status = 'active'
            LIMIT 1
            """,
            (
                administration_id,
                context.user_id,
            ),
        ).fetchone()

        if current_authority is None:
            return AuthorizationDecision(
                allowed=False,
                reason="no active authority assignment",
            )

        try:
            role = AuthorityRole(current_authority["role"])
        except (TypeError, ValueError):
            return AuthorizationDecision(
                allowed=False,
                reason="invalid authority role",
            )

        authority = Authority(
            actor_id=context.user_id,
            actor_type=ActorType.HUMAN,
            role=role,
            jurisdiction_type=JurisdictionType.ADMINISTRATION,
            jurisdiction_id=str(administration_id),
            administration_id=str(administration_id),
        )

        request = AuthorizationRequest(
            authority=authority,
            action=action,
            resource_type=resource_type,
            resource_id=(
                resource_id
                if resource_id is not None
                else str(administration_id)
            ),
        )

        allowed, reason = evaluate(request)

        return AuthorizationDecision(
            allowed=allowed,
            reason=reason,
        )
