from services.application_service_factory import ApplicationServiceFactory
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.parent_service import ParentService
from services.parent_student_service import ParentStudentService


class ApplicationServices:
    """
    Application-scoped service container.

    The container owns one application service graph for one database
    connection. Telegram handlers should obtain application services
    through this boundary rather than constructing repositories/services
    directly.

    Each service is constructed once when the container is initialized
    and the same instance is returned for the lifetime of the container.
    """

    def __init__(self, factory: ApplicationServiceFactory):
        self.factory = factory

        self._verification_workflow = (
            factory.build_verification_workflow_service()
        )
        self._verification = factory.build_verification_service()
        self._service_act = factory.build_service_act_service()
        self._talent_point_issuance = (
            factory.build_talent_point_issuance_service()
        )
        self._talent_point_transfer = (
            factory.build_talent_point_transfer_service()
        )
        self._dispute = factory.build_dispute_service()
        self._reputation = factory.build_reputation_service()
        self._reputation_profile = (
            factory.build_reputation_profile_service()
        )

    @property
    def verification_workflow(self):
        return self._verification_workflow

    @property
    def verification(self):
        return self._verification

    @property
    def service_act(self):
        return self._service_act

    @property
    def talent_point_issuance(self):
        return self._talent_point_issuance

    @property
    def talent_point_transfer(self):
        return self._talent_point_transfer

    @property
    def dispute(self):
        return self._dispute

    @property
    def reputation(self):
        return self._reputation

    @property
    def reputation_profile(self):
        return self._reputation_profile

    def attendance(self, tenant_id: str, user_id=None):
        return AttendanceService(
            repository=self.factory.build_attendance_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def student(self, tenant_id: str, user_id=None):
        return StudentService(
            repository=self.factory.build_student_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def teacher(self, tenant_id: str, user_id=None):
        return TeacherService(
            repository=self.factory.build_teacher_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def parent(self, tenant_id: str, user_id=None):
        return ParentService(
            repository=self.factory.build_parent_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def parent_student(self, tenant_id: str, user_id=None):
        return ParentStudentService(
            repository=self.factory.build_parent_student_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )
