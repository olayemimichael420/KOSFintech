from models.teaching_session_subject import TeachingSessionSubject


class TeachingSessionSubjectService:
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

    def _require(self, permission):
        if self.connection is None or self.user_id is None:
            return

        from services.permission_resolution_service import PermissionResolutionService

        resolver = PermissionResolutionService(self.connection)

        if not resolver.has_permission(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            permission_name=permission,
        ):
            raise PermissionError(permission)

    def create(
        self,
        offering: TeachingSessionSubject,
    ) -> TeachingSessionSubject:
        self._require("teaching_session_subject.write")

        if offering.tenant_id != self.tenant_id:
            raise ValueError("teaching session subject tenant mismatch")

        return self.repository.create(offering)

    def get(self, offering_id: int):
        self._require("teaching_session_subject.read")
        return self.repository.get(self.tenant_id, offering_id)

    def list(self, teaching_session_id: int):
        self._require("teaching_session_subject.read")
        return self.repository.list(
            self.tenant_id,
            teaching_session_id,
        )
