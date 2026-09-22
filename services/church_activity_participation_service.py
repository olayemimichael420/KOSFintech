from services.permission_resolution_service import PermissionResolutionService


class ChurchActivityParticipationService:
    READ_PERMISSION = "church_activity_participation.read"
    WRITE_PERMISSION = "church_activity_participation.write"

    def __init__(
        self,
        repository,
        tenant_id: str,
        connection=None,
        user_id=None,
    ):
        self.repository = repository
        self.tenant_id = tenant_id
        self.connection = connection
        self.user_id = user_id

        if connection is not None:
            self.permission_service = PermissionResolutionService(connection)
        else:
            self.permission_service = None

    def _require_permission(self, permission_name: str) -> None:
        if self.permission_service is None or self.user_id is None:
            return

        if not self.permission_service.has_permission(
            user_id=self.user_id,
            permission_name=permission_name,
            tenant_id=self.tenant_id,
        ):
            raise PermissionError(
                f"missing permission: {permission_name}"
            )

    def create(self, participation):
        self._require_permission(self.WRITE_PERMISSION)

        if participation.tenant_id != self.tenant_id:
            raise ValueError(
                "church activity participation tenant mismatch"
            )

        return self.repository.create(participation)

    def get(
        self,
        church_activity_id: int,
        membership_id: int,
    ):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.get(
            self.tenant_id,
            church_activity_id,
            membership_id,
        )

    def list_by_activity(
        self,
        church_activity_id: int,
    ):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.list_by_activity(
            self.tenant_id,
            church_activity_id,
        )

    def list_by_member(
        self,
        membership_id: int,
    ):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.list_by_member(
            self.tenant_id,
            membership_id,
        )
