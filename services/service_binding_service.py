from models.service_binding import ServiceBinding
from repositories.service_binding_repository import ServiceBindingRepository
from repositories.tenant_repository import TenantRepository


class ServiceBindingService:
    def __init__(
        self,
        repository: ServiceBindingRepository,
        tenant_repository: TenantRepository,
    ):
        self.repository = repository
        self.tenant_repository = tenant_repository

    def create(
        self,
        institution_anchor_id: int,
        tenant_id: str,
        status: str = "active",
    ) -> ServiceBinding:
        if status not in {"active", "inactive"}:
            raise ValueError("invalid service binding status")

        if self.tenant_repository.get_by_tenant_id(tenant_id) is None:
            raise ValueError("tenant not found")

        binding = ServiceBinding(
            id=None,
            institution_anchor_id=institution_anchor_id,
            tenant_id=tenant_id,
            status=status,
        )

        return self.repository.create(binding)

    def get(self, binding_id: int):
        return self.repository.get(binding_id)

    def list_active(self) -> list[ServiceBinding]:
        return self.repository.list_active()
