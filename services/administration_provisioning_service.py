from models.administration import Administration
from repositories.administration_repository import AdministrationRepository
from repositories.tenant_repository import TenantRepository


class AdministrationProvisioningService:
    """
    Platform-level administration provisioning boundary.

    This service creates the tenant-bound Administration record.
    It does not create institutional provenance, service bindings,
    administration authority, or RBAC authority.
    """

    def __init__(
        self,
        repository: AdministrationRepository,
        tenant_repository: TenantRepository,
    ):
        self.repository = repository
        self.tenant_repository = tenant_repository

    def create(
        self,
        tenant_id: str,
        name: str,
        administration_type: str,
    ) -> Administration:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        if self.tenant_repository.get_by_tenant_id(tenant_id) is None:
            raise ValueError("tenant not found")

        if not name.strip():
            raise ValueError("name is required")

        if not administration_type.strip():
            raise ValueError("administration_type is required")

        administration = Administration(
            id=None,
            tenant_id=tenant_id,
            name=name,
            administration_type=administration_type,
        )

        return self.repository.create(administration)
