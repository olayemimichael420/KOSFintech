from models.academic_session import AcademicSession
from services.permission_resolution_service import PermissionResolutionService


class AcademicSessionService:
    READ_PERMISSION = "academic_session.read"
    WRITE_PERMISSION = "academic_session.write"

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

    def create(self, session: AcademicSession) -> AcademicSession:
        self._require_permission(self.WRITE_PERMISSION)

        if session.tenant_id != self.tenant_id:
            raise ValueError("academic session tenant mismatch")

        if session.start_date > session.end_date:
            raise ValueError(
                "academic session start date must not be after end date"
            )

        return self.repository.create(session)

    def list(self):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.list(self.tenant_id)

    def get(self, session_id: int):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.get(
            self.tenant_id,
            session_id,
        )
