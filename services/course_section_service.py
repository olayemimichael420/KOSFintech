from models.course_section import CourseSection
from services.permission_resolution_service import PermissionResolutionService


class CourseSectionService:
    READ_PERMISSION = "course_section.read"
    WRITE_PERMISSION = "course_section.write"

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

    def create(self, section: CourseSection) -> CourseSection:
        self._require_permission(self.WRITE_PERMISSION)

        if section.tenant_id != self.tenant_id:
            raise ValueError("course section tenant mismatch")

        return self.repository.create(section)

    def list(self, course_offering_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list(
            self.tenant_id,
            course_offering_id,
        )

    def get(self, section_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            section_id,
        )
