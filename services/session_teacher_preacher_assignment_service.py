from models.session_teacher_preacher_assignment import (
    SessionTeacherPreacherAssignment,
)
from services.permission_resolution_service import PermissionResolutionService


class SessionTeacherPreacherAssignmentService:
    """
    CMOS teaching/preaching session assignment service.

    This service records assignment of an existing Teacher/Preacher
    capacity to a bounded TeachingSession.

    This does not establish leadership, responsibility, participation,
    attendance, learning, competence, assessment, score, grade, result,
    progress, appointment, ordination, ecclesiastical authority,
    authentication, or application authorization.
    """

    READ_PERMISSION = "session_teacher_preacher_assignment.read"
    WRITE_PERMISSION = "session_teacher_preacher_assignment.write"

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

    def create(
        self,
        assignment: SessionTeacherPreacherAssignment,
    ) -> SessionTeacherPreacherAssignment:
        self._require_permission(self.WRITE_PERMISSION)

        if assignment.tenant_id != self.tenant_id:
            raise ValueError(
                "session teacher/preacher assignment tenant mismatch"
            )

        return self.repository.create(assignment)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list(self.tenant_id)

    def get(self, assignment_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            assignment_id,
        )
