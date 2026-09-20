from models.teaching_content import TeachingContent
from repositories.teaching_focus_repository import TeachingFocusRepository
from services.permission_resolution_service import PermissionResolutionService


class TeachingContentService:
    READ_PERMISSION = "teaching_content.read"
    WRITE_PERMISSION = "teaching_content.write"

    def __init__(
        self,
        repository,
        tenant_id: str,
        connection=None,
        user_id=None,
        focus_repository=None,
    ):
        self.repository = repository
        self.tenant_id = tenant_id
        self.connection = connection
        self.user_id = user_id

        if focus_repository is not None:
            self.focus_repository = focus_repository
        elif connection is not None:
            self.focus_repository = TeachingFocusRepository(connection)
        else:
            self.focus_repository = None

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

    def create(self, content: TeachingContent) -> TeachingContent:
        self._require_permission(self.WRITE_PERMISSION)

        if content.tenant_id != self.tenant_id:
            raise ValueError("teaching content tenant mismatch")

        if self.focus_repository is None:
            raise ValueError("teaching focus repository is required")

        focus = self.focus_repository.get(
            self.tenant_id,
            content.teaching_focus_id,
        )

        if focus is None:
            raise ValueError("teaching focus not found")

        return self.repository.create(content)

    def list(self, teaching_focus_id: int):
        self._require_permission(self.READ_PERMISSION)

        if self.focus_repository is None:
            raise ValueError("teaching focus repository is required")

        focus = self.focus_repository.get(
            self.tenant_id,
            teaching_focus_id,
        )

        if focus is None:
            return []

        return self.repository.list(
            self.tenant_id,
            teaching_focus_id,
        )

    def get(self, content_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(self.tenant_id, content_id)
