from models.teaching_focus import TeachingFocus
from repositories.teaching_series_repository import TeachingSeriesRepository
from services.permission_resolution_service import PermissionResolutionService


class TeachingFocusService:
    READ_PERMISSION = "teaching_focus.read"
    WRITE_PERMISSION = "teaching_focus.write"

    def __init__(
        self,
        repository,
        tenant_id: str,
        connection=None,
        user_id=None,
        series_repository=None,
    ):
        self.repository = repository
        self.tenant_id = tenant_id
        self.connection = connection
        self.user_id = user_id

        if series_repository is not None:
            self.series_repository = series_repository
        elif connection is not None:
            self.series_repository = TeachingSeriesRepository(connection)
        else:
            self.series_repository = None

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

    def create(self, focus: TeachingFocus) -> TeachingFocus:
        self._require_permission(self.WRITE_PERMISSION)

        if focus.tenant_id != self.tenant_id:
            raise ValueError("teaching focus tenant mismatch")

        if focus.start_date > focus.end_date:
            raise ValueError(
                "teaching focus start date must not be after end date"
            )

        if self.series_repository is None:
            raise ValueError("teaching series repository is required")

        series = self.series_repository.get(
            self.tenant_id,
            focus.teaching_series_id,
        )

        if series is None:
            raise ValueError("teaching series not found")

        if focus.start_date < series.start_date:
            raise ValueError(
                "teaching focus start date must be within teaching series"
            )

        if focus.end_date > series.end_date:
            raise ValueError(
                "teaching focus end date must be within teaching series"
            )

        return self.repository.create(focus)

    def list(self, teaching_series_id: int):
        self._require_permission(self.READ_PERMISSION)

        if self.series_repository is None:
            raise ValueError("teaching series repository is required")

        series = self.series_repository.get(
            self.tenant_id,
            teaching_series_id,
        )

        if series is None:
            return []

        return self.repository.list(
            self.tenant_id,
            teaching_series_id,
        )

    def get(self, focus_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(self.tenant_id, focus_id)
