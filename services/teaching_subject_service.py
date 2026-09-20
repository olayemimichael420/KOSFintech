from models.teaching_subject import TeachingSubject
from services.permission_resolution_service import PermissionResolutionService


class TeachingSubjectService:
    READ_PERMISSION = "teaching_subject.read"
    WRITE_PERMISSION = "teaching_subject.write"

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

    def create(self, subject: TeachingSubject) -> TeachingSubject:
        self._require_permission(self.WRITE_PERMISSION)

        if subject.tenant_id != self.tenant_id:
            raise ValueError("teaching subject tenant mismatch")

        return self.repository.create(subject)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list(self.tenant_id)

    def get(self, subject_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            subject_id,
        )
