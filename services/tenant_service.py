from models.tenant import Tenant
from repositories.tenant_repository import TenantRepository
from services.tenant_identity_generator import TenantIdentityGenerator


class TenantService:
    """
    KOSFintech tenant service boundary.

    A tenant represents a service-isolation boundary.
    This service does not establish institutional provenance,
    confer authority, create administration authority,
    or grant authorization.
    """

    def __init__(
        self,
        repository: TenantRepository,
        identity_generator: TenantIdentityGenerator | None = None,
    ):
        self.repository = repository
        self.identity_generator = (
            identity_generator
            if identity_generator is not None
            else TenantIdentityGenerator()
        )

    def create(
        self,
        tenant_id: str | None = None,
        status: str = "active",
    ) -> Tenant:
        if tenant_id is None:
            tenant_id = self.identity_generator.generate()

        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        if status not in {"active", "inactive"}:
            raise ValueError("invalid tenant status")

        tenant = Tenant(
            id=None,
            tenant_id=tenant_id,
            status=status,
        )

        return self.repository.create(tenant)

    def get(self, tenant_id: str, tenant_pk: int):
        return self.repository.get(tenant_id, tenant_pk)

    def list_active(self) -> list[Tenant]:
        return self.repository.list_active()
