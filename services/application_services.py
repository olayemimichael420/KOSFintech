from services.application_service_factory import ApplicationServiceFactory
from services.attendance_service import AttendanceService
from services.academic_session_service import AcademicSessionService
from services.course_offering_service import CourseOfferingService
from services.course_section_service import CourseSectionService
from services.academic_term_service import AcademicTermService
from services.academic_class_service import AcademicClassService
from services.academic_subject_service import AcademicSubjectService
from services.teacher_subject_assignment_service import TeacherSubjectAssignmentService
from services.student_enrollment_service import StudentEnrollmentService
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.parent_service import ParentService
from services.parent_student_service import ParentStudentService
from services.teacher_student_service import TeacherStudentService
from services.school_student_service import SchoolStudentService
from services.external_identity_service import ExternalIdentityService
from services.authentication_service import AuthenticationService
from services.authorization_context_service import AuthorizationContextService
from services.authorization_service import AuthorizationService
from services.administration_context_service import AdministrationContextService
from services.rbac_provisioning_service import RBACProvisioningService
from services.telegram_identity_service import TelegramIdentityService
from services.telegram_channel_binding_service import TelegramChannelBindingService


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
        self._service_request = factory.build_service_request_service()
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
        self._authentication = factory.build_authentication_service()
        self._authorization_context = (
            factory.build_authorization_context_service()
        )
        self._authorization = factory.build_authorization_service()
        self._administration_context = (
            factory.build_administration_context_service()
        )
        self._rbac_provisioning = (
            factory.build_rbac_provisioning_service()
        )
        self._telegram_channel_binding = (
            factory.build_telegram_channel_binding_service()
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
    def service_request(self):
        return self._service_request

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
    @property
    def authentication(self):
        return self._authentication

    @property
    def telegram_identity(self) -> TelegramIdentityService:
        return self.factory.build_telegram_identity_service()

    @property
    def telegram_channel_binding(self) -> TelegramChannelBindingService:
        return self._telegram_channel_binding

    @property
    def authorization_context(self) -> AuthorizationContextService:
        return self._authorization_context

    @property
    def authorization(self) -> AuthorizationService:
        return self._authorization

    @property
    def administration_context(self) -> AdministrationContextService:
        return self._administration_context

    @property
    def rbac_provisioning(self) -> RBACProvisioningService:
        return self._rbac_provisioning

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

    def teacher_student(self, tenant_id: str, user_id=None):
        return TeacherStudentService(
            repository=self.factory.build_teacher_student_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def school_student(self, tenant_id: str, user_id=None):
        return SchoolStudentService(
            repository=self.factory.build_school_student_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    @property
    def external_identity(self):
        return self.factory.build_external_identity_service()


    def course_offering(self, tenant_id: str, user_id=None):
        return CourseOfferingService(
            repository=self.factory.build_course_offering_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def course_section(self, tenant_id: str, user_id=None):
        return CourseSectionService(
            repository=self.factory.build_course_section_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def academic_session(self, tenant_id: str, user_id=None):
        return AcademicSessionService(
            repository=self.factory.build_academic_session_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def academic_term(self, tenant_id: str, user_id=None):
        return AcademicTermService(
            repository=self.factory.build_academic_term_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def academic_class(self, tenant_id: str, user_id=None):
        return AcademicClassService(
            repository=self.factory.build_academic_class_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def academic_subject(self, tenant_id: str, user_id=None):
        return AcademicSubjectService(
            repository=self.factory.build_academic_subject_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def teacher_subject_assignment(
        self,
        tenant_id: str,
        user_id=None,
    ):
        return TeacherSubjectAssignmentService(
            repository=self.factory.build_teacher_subject_assignment_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )

    def student_enrollment(self, tenant_id: str, user_id=None):
        return StudentEnrollmentService(
            repository=self.factory.build_student_enrollment_repository(),
            tenant_id=tenant_id,
            connection=self.factory.connection,
            user_id=user_id,
        )
