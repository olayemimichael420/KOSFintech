from models.teaching_series import TeachingSeries
from repositories.teaching_session_repository import TeachingSessionRepository
from services.permission_resolution_service import PermissionResolutionService


class TeachingSeriesService:
    READ_PERMISSION = "teaching_series.read"
    WRITE_PERMISSION = "teaching_series.write"

    def __init__(
        self,
        repository,
        tenant_id: str,
        connection=None,
        user_id=None,
        session_repository=None,
    ):
        self.repository = repository
        self.tenant_id = tenant_id
        self.connection = connection
        self.user_id = user_id

        if session_repository is not None:
            self.session_repository = session_repository
        elif connection is not None:
            self.session_repository = TeachingSessionRepository(connection)
        else:
            self.session_repository = None

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

    def create(self, series: TeachingSeries) -> TeachingSeries:
        self._require_permission(self.WRITE_PERMISSION)

        if series.tenant_id != self.tenant_id:
            raise ValueError("teaching series tenant mismatch")

        if series.start_date > series.end_date:
            raise ValueError(
                "teaching series start date must not be after end date"
            )

        if self.session_repository is None:
            raise ValueError(
                "teaching session repository is required"
            )

        session = self.session_repository.get(
            self.tenant_id,
            series.teaching_session_id,
        )

        if session is None:
            raise ValueError("teaching session not found")

        if series.start_date < session.start_date:
            raise ValueError(
                "teaching series start date must be within teaching session"
            )

        if series.end_date > session.end_date:
            raise ValueError(
                "teaching series end date must be within teaching session"
            )

        return self.repository.create(series)

    def list(self, teaching_session_id: int):
        self._require_permission(self.READ_PERMISSION)

        if self.session_repository is None:
            raise ValueError(
                "teaching session repository is required"
            )

        session = self.session_repository.get(
            self.tenant_id,
            teaching_session_id,
        )

        if session is None:
            return []

        return self.repository.list(
            self.tenant_id,
            teaching_session_id,
        )

    def get(self, series_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(self.tenant_id, series_id)
