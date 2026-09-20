from models.assessment_score import AssessmentScore
from services.permission_resolution_service import PermissionResolutionService


class AssessmentScoreService:
    READ_PERMISSION = "assessment_score.read"
    WRITE_PERMISSION = "assessment_score.write"

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

    def record(
        self,
        assessment_score: AssessmentScore,
    ) -> AssessmentScore:
        self._require_permission(self.WRITE_PERMISSION)

        if assessment_score.tenant_id != self.tenant_id:
            raise ValueError("assessment score tenant mismatch")

        return self.repository.create(assessment_score)

    def list(self):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_tenant(self.tenant_id)

    def list_by_assessment(self, assessment_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_assessment(
            self.tenant_id,
            assessment_id,
        )

    def list_by_member(self, membership_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.list_by_member(
            self.tenant_id,
            membership_id,
        )

    def get(self, assessment_score_id: int):
        self._require_permission(self.READ_PERMISSION)
        return self.repository.get(
            self.tenant_id,
            assessment_score_id,
        )
