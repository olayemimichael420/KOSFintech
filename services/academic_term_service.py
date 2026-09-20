from models.academic_term import AcademicTerm
from services.permission_resolution_service import PermissionResolutionService


class AcademicTermService:
    READ_PERMISSION = "academic_term.read"
    WRITE_PERMISSION = "academic_term.write"

    def __init__(
        self,
        repository,
        academic_session_repository,
        tenant_id: str,
        connection=None,
        user_id=None,
    ):
        self.repository = repository
        self.academic_session_repository = academic_session_repository
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

    def create(self, term: AcademicTerm) -> AcademicTerm:
        self._require_permission(self.WRITE_PERMISSION)

        if term.tenant_id != self.tenant_id:
            raise ValueError("academic term tenant mismatch")

        if term.start_date > term.end_date:
            raise ValueError(
                "academic term start date must not be after end date"
            )

        session = self.academic_session_repository.get(
            self.tenant_id,
            term.academic_session_id,
        )

        if session is None:
            raise ValueError("academic session not found")

        if term.start_date < session.start_date:
            raise ValueError(
                "academic term must start on or after academic session start date"
            )

        if term.end_date > session.end_date:
            raise ValueError(
                "academic term must end on or before academic session end date"
            )

        return self.repository.create(term)

    def list(self, academic_session_id: int):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.list(
            self.tenant_id,
            academic_session_id,
        )

    def get(self, term_id: int):
        self._require_permission(self.READ_PERMISSION)

        return self.repository.get(
            self.tenant_id,
            term_id,
        )
