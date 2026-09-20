from models.teaching_session_attendance import TeachingSessionAttendance
from services.permission_resolution_service import PermissionResolutionService


class TeachingSessionAttendanceService:
    ALLOWED_STATUSES = {
        "present",
        "absent",
        "late",
        "excused",
    }

    READ_PERMISSION = "teaching_session_attendance.read"
    WRITE_PERMISSION = "teaching_session_attendance.write"

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
        """
        Enforce application RBAC when an authenticated user context
        is supplied.

        Service-only construction remains supported so repository-focused
        tests and internal callers are not broken.
        """
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

    def record(
        self,
        attendance: TeachingSessionAttendance,
    ) -> TeachingSessionAttendance:
        self._require_permission(self.WRITE_PERMISSION)

        if attendance.status not in self.ALLOWED_STATUSES:
            raise ValueError("invalid teaching session attendance status")

        if attendance.tenant_id != self.tenant_id:
            raise ValueError(
                "teaching session attendance tenant mismatch"
            )

        return self.repository.create(attendance)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_tenant(
            self.tenant_id,
        )

    def list_by_session(self, teaching_session_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_session(
            self.tenant_id,
            teaching_session_id,
        )

    def list_by_member(self, membership_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_member(
            self.tenant_id,
            membership_id,
        )

    def list_by_date(self, attendance_date: str):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_date(
            self.tenant_id,
            attendance_date,
        )

    def get(self, attendance_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            attendance_id,
        )
