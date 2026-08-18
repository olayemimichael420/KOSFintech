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

        assignment = (
            self.repository.get_active_by_user_and_administration(
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
