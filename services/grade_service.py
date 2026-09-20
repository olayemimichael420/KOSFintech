from models.grade import Grade
from services.permission_resolution_service import PermissionResolutionService


class GradeService:
    READ_PERMISSION = "grade.read"
    WRITE_PERMISSION = "grade.write"

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

    def record(self, grade: Grade) -> Grade:
        self._require_permission(self.WRITE_PERMISSION)

        if grade.tenant_id != self.tenant_id:
            raise ValueError("grade tenant mismatch")

        return self.repository.create(grade)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_tenant(self.tenant_id)

    def get(self, grade_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(self.tenant_id, grade_id)
