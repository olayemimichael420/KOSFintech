from repositories.external_identity_repository import ExternalIdentityRepository
from repositories.user_repository import UserRepository
from models.external_identity import ExternalIdentity
from services.permission_resolution_service import PermissionResolutionService


class ExternalIdentityService:
    """
    Binds external identities to existing canonical KOSFintech users.

    This service does not provision users, tenants, roles, permissions,
    administration authority, or governance authority.
    """

    READ_PERMISSION = "external_identity.read"
    LINK_PERMISSION = "external_identity.link"

    def __init__(
        self,
        external_identity_repository: ExternalIdentityRepository,
        user_repository: UserRepository,
        permission_service: PermissionResolutionService,
    ):
        self.external_identity_repository = external_identity_repository
        self.user_repository = user_repository
        self.permission_service = permission_service

    def link(
        self,
        provider: str,
        subject: str,
        tenant_id: str,
        user_id: int,
        actor_user_id: int,
    ) -> ExternalIdentity:
        """
        Link an external provider identity to an existing active user.
        The actor must hold the explicit application permission.
        """

        if not self.permission_service.has_permission(
            user_id=actor_user_id,
            permission_name=self.LINK_PERMISSION,
            tenant_id=tenant_id,
        ):
            raise PermissionError("external identity link permission denied")

        user = self.user_repository.get(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        if user is None:
            raise ValueError("canonical user not found")

        if user.status != "active":
            raise ValueError("canonical user is not active")

        if user.tenant_id != tenant_id:
            raise ValueError("user tenant mismatch")

        existing = (
            self.external_identity_repository.get_by_provider_subject(
                provider=provider,
                subject=subject,
            )
        )

        if existing is not None:
            raise ValueError("external identity already linked")

        identity = ExternalIdentity(
            id=None,
            provider=provider,
            subject=subject,
            tenant_id=user.tenant_id,
            user_id=user.id,
        )

        return self.external_identity_repository.create(identity)

    def resolve(
        self,
        provider: str,
        subject: str,
    ):
        """
        Resolve an external identity to its canonical identity binding.
        """

        return self.external_identity_repository.get_by_provider_subject(
            provider=provider,
            subject=subject,
        )

    def list_for_user(
        self,
        tenant_id: str,
        user_id: int,
        actor_user_id: int,
    ):
        """
        List external identities belonging to a tenant-scoped user.

        The caller must hold the explicit external identity read
        permission within the authenticated tenant.
        """

        if not self.permission_service.has_permission(
            user_id=actor_user_id,
            permission_name=self.READ_PERMISSION,
            tenant_id=tenant_id,
        ):
            raise PermissionError(
                "external identity read permission denied"
            )

        user = self.user_repository.get(
            tenant_id=tenant_id,
            user_id=user_id,
        )

        if user is None:
            raise ValueError("canonical user not found")

        return self.external_identity_repository.list_by_user(
            tenant_id=tenant_id,
            user_id=user_id,
        )
