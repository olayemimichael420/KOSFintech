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
            SELECT tenant_id
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

        # Platform authority is distinct from administration authority.
        if context.is_super_admin:
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

        if not context.has_administration_authority:
            return AuthorizationDecision(
                allowed=False,
                reason="no active authority assignment",
            )

        try:
            role = AuthorityRole(context.administration_role)
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
