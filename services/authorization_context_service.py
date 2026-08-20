from dataclasses import dataclass
from typing import Optional

from repositories.administration_authority_repository import (
    AdministrationAuthorityRepository,
)
from repositories.platform_authority_repository import PlatformAuthorityRepository


@dataclass(frozen=True)
class AuthorizationContext:
    """Resolved authority context for an authenticated KOSFintech user."""

    user_id: int
    platform_role: Optional[str] = None
    administration_id: Optional[int] = None
    administration_role: Optional[str] = None

    @property
    def is_super_admin(self) -> bool:
        return self.platform_role == "super_admin"

    @property
    def has_administration_authority(self) -> bool:
        return self.administration_role in {
            "owner",
            "admin1",
            "admin2",
        }


class AuthorizationContextService:
    """
    Resolve database-backed authority for a KOSFintech user.

    This service deliberately does not infer governance authority from
    users.role, application roles, Telegram identity, or other metadata.
    """

    def __init__(self, connection):
        self.connection = connection
        self.platform_repository = PlatformAuthorityRepository(connection)
        self.administration_repository = AdministrationAuthorityRepository(
            connection
        )

    def resolve(
        self,
        user_id: int,
        administration_id: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> AuthorizationContext:
        # The authenticated user's database record is authoritative.
        # Inactive or missing users cannot hold effective governance
        # authority, even if a stale authority row still exists.
        user_row = self.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None or user_row["status"] != "active":
            return AuthorizationContext(
                user_id=user_id,
                administration_id=administration_id,
            )

        platform_authority = self.platform_repository.get_active_by_user(user_id)

        platform_role = (
            platform_authority.role.value
            if platform_authority is not None
            else None
        )

        if administration_id is None:
            return AuthorizationContext(
                user_id=user_id,
                platform_role=platform_role,
            )

        # The authenticated user's tenant is authoritative.
        # A caller-supplied tenant_id may confirm that tenant, but must
        # never override or replace it. Application roles are never used
        # as governance authority.

        authenticated_tenant_id = user_row["tenant_id"]

        if (
            tenant_id is not None
            and tenant_id != authenticated_tenant_id
        ):
            return AuthorizationContext(
                user_id=user_id,
                platform_role=platform_role,
                administration_id=administration_id,
            )

        tenant_id = authenticated_tenant_id

        administration_authority = (
            self.administration_repository
            .get_active_by_user_and_administration(
                tenant_id=tenant_id,
                user_id=user_id,
                administration_id=administration_id,
            )
        )

        administration_role = (
            administration_authority.role.value
            if administration_authority is not None
            else None
        )

        return AuthorizationContext(
            user_id=user_id,
            platform_role=platform_role,
            administration_id=administration_id,
            administration_role=administration_role,
        )
