from models.course_offering import CourseOffering
from services.permission_resolution_service import PermissionResolutionService


class CourseOfferingService:
    READ_PERMISSION = "course_offering.read"
    WRITE_PERMISSION = "course_offering.write"

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

    def create(self, offering: CourseOffering) -> CourseOffering:
        self._require_permission(self.WRITE_PERMISSION)

        if offering.tenant_id != self.tenant_id:
            raise ValueError("course offering tenant mismatch")

        return self.repository.create(offering)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list(self.tenant_id)

    def get(self, offering_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            offering_id,
        )
