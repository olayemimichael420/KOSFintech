from repositories.service_act_repository import ServiceActRepository
from repositories.service_request_repository import ServiceRequestRepository
from repositories.verification_repository import VerificationRepository
from repositories.talent_point_repository import TalentPointRepository
from repositories.dispute_repository import DisputeRepository
from repositories.reputation_repository import ReputationRepository
from repositories.attendance_repository import AttendanceRepository
from repositories.student_repository import StudentRepository
from repositories.teacher_repository import TeacherRepository
from repositories.parent_repository import ParentRepository
from repositories.parent_student_repository import ParentStudentRepository
from repositories.teacher_student_repository import TeacherStudentRepository
from repositories.school_student_repository import SchoolStudentRepository
from repositories.external_identity_repository import ExternalIdentityRepository
from repositories.telegram_channel_binding_repository import TelegramChannelBindingRepository
from repositories.user_repository import UserRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.course_offering_repository import CourseOfferingRepository
from repositories.course_section_repository import CourseSectionRepository
from repositories.section_teacher_assignment_repository import SectionTeacherAssignmentRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.teacher_subject_assignment_repository import TeacherSubjectAssignmentRepository
from repositories.student_enrollment_repository import StudentEnrollmentRepository

from services.service_act_service import ServiceActService
from services.service_request_service import ServiceRequestService
from services.verification_service import VerificationService
from services.verification_decision_service import VerificationDecisionService
from services.service_act_verification_service import ServiceActVerificationService
from services.verification_workflow_service import VerificationWorkflowService
from services.talent_point_issuance_service import TalentPointIssuanceService
from services.talent_point_transfer_service import TalentPointTransferService
from services.dispute_service import DisputeService
from services.reputation_service import ReputationService
from services.reputation_profile_service import ReputationProfileService
from services.external_identity_service import ExternalIdentityService
from services.permission_resolution_service import PermissionResolutionService
from services.authentication_service import AuthenticationService
from services.authorization_context_service import AuthorizationContextService
from services.authorization_service import AuthorizationService
from services.administration_context_service import AdministrationContextService
from services.rbac_provisioning_service import RBACProvisioningService
from services.telegram_identity_service import TelegramIdentityService
from services.telegram_channel_binding_service import TelegramChannelBindingService


class ApplicationServiceFactory:
    """
    Composition root for KOSFintech application services.

    The factory constructs one coherent application service graph from
    one database connection.

    Repositories are constructed once.
    Services are constructed once.
    Composite services receive the already-constructed dependencies.

    Business logic remains inside services; dependency wiring remains here.
    """

    def __init__(self, connection):
        self.connection = connection

        # ---------------------------------------------------------------
        # Repository graph
        # ---------------------------------------------------------------

        self._service_act_repository = ServiceActRepository(connection)
        self._service_request_repository = ServiceRequestRepository(connection)
        self._verification_repository = VerificationRepository(connection)
        self._talent_point_repository = TalentPointRepository(connection)
        self._dispute_repository = DisputeRepository(connection)
        self._reputation_repository = ReputationRepository(connection)
        self._attendance_repository = AttendanceRepository(connection)
        self._student_repository = StudentRepository(connection)
        self._teacher_repository = TeacherRepository(connection)
        self._parent_repository = ParentRepository(connection)
        self._parent_student_repository = ParentStudentRepository(connection)
        self._teacher_student_repository = TeacherStudentRepository(connection)
        self._school_student_repository = SchoolStudentRepository(connection)
        self._external_identity_repository = ExternalIdentityRepository(connection)
        self._telegram_channel_binding_repository = TelegramChannelBindingRepository(connection)
        self._user_repository = UserRepository(connection)
        self._academic_session_repository = AcademicSessionRepository(connection)
        self._course_offering_repository = CourseOfferingRepository(connection)
        self._course_section_repository = CourseSectionRepository(connection)
        self._section_teacher_assignment_repository = SectionTeacherAssignmentRepository(connection)
        self._academic_term_repository = AcademicTermRepository(connection)
        self._academic_class_repository = AcademicClassRepository(connection)
        self._academic_subject_repository = AcademicSubjectRepository(connection)
        self._teacher_subject_assignment_repository = TeacherSubjectAssignmentRepository(connection)
        self._student_enrollment_repository = StudentEnrollmentRepository(connection)

        # ---------------------------------------------------------------
        # Core authorization service
        # ---------------------------------------------------------------

        self._permission_resolution_service = PermissionResolutionService(
            connection
        )
        self._authentication_service = AuthenticationService(
            connection
        )
        self._authorization_context_service = AuthorizationContextService(
            connection
        )
        self._authorization_service = AuthorizationService(
            connection
        )
        self._administration_context_service = AdministrationContextService(
            connection
        )
        self._rbac_provisioning_service = RBACProvisioningService(
            connection=connection,
            authorization_service=self._authorization_service,
        )

        # ---------------------------------------------------------------
        # Core service graph
        # ---------------------------------------------------------------

        self._service_act_service = ServiceActService(
            self._service_act_repository,
            self._permission_resolution_service,
        )
        self._service_request_service = ServiceRequestService(
            self._service_request_repository,
            self._permission_resolution_service,
        )


        self._verification_service = VerificationService(
            repository=self._verification_repository,
            service_act_repository=self._service_act_repository,
            permission_service=self._permission_resolution_service,
        )

        self._verification_decision_service = VerificationDecisionService(
            self._verification_repository
        )

        self._service_act_verification_service = (
            ServiceActVerificationService(
                verification_decision_service=(
                    self._verification_decision_service
                ),
                service_act_service=self._service_act_service,
            )
        )

        self._verification_workflow_service = VerificationWorkflowService(
            verification_service=self._verification_service,
            service_act_verification_service=(
                self._service_act_verification_service
            ),
        )

        self._talent_point_issuance_service = (
            TalentPointIssuanceService(
                repository=self._talent_point_repository,
                permission_service=self._permission_resolution_service,
            )
        )
        self._talent_point_transfer_service = (
            TalentPointTransferService(
                repository=self._talent_point_repository,
                permission_service=self._permission_resolution_service,
            )
        )

        self._dispute_service = DisputeService(
            repository=self._dispute_repository,
            service_act_repository=self._service_act_repository,
        )

        self._reputation_service = ReputationService(
            repository=self._reputation_repository,
            service_act_repository=self._service_act_repository,
        )

        self._reputation_profile_service = ReputationProfileService(
            repository=self._reputation_repository,
        )


        self._external_identity_service = ExternalIdentityService(
            external_identity_repository=self._external_identity_repository,
            user_repository=self._user_repository,
            permission_service=self._permission_resolution_service,
        )

        self._telegram_channel_binding_service = TelegramChannelBindingService(
            self._telegram_channel_binding_repository
        )


        self._telegram_identity_service = TelegramIdentityService(
            external_identity_service=self._external_identity_service,
            authentication_service=self._authentication_service,
        )

    # -------------------------------------------------------------------
    # Repository access
    # -------------------------------------------------------------------

    def build_service_act_repository(self):
        return self._service_act_repository
    def build_service_request_repository(self):
        return self._service_request_repository


    def build_verification_repository(self):
        return self._verification_repository

    def build_talent_point_repository(self):
        return self._talent_point_repository

    def build_dispute_repository(self):
        return self._dispute_repository

    def build_reputation_repository(self):
        return self._reputation_repository

    def build_attendance_repository(self):
        return self._attendance_repository

    def build_student_repository(self):
        return self._student_repository

    def build_teacher_repository(self):
        return self._teacher_repository

    def build_parent_repository(self):
        return self._parent_repository

    def build_parent_student_repository(self):
        return self._parent_student_repository

    def build_teacher_student_repository(self):
        return self._teacher_student_repository

    def build_school_student_repository(self):
        return self._school_student_repository

    def build_external_identity_repository(self):
        return self._external_identity_repository

    def build_user_repository(self):
        return self._user_repository

    def build_course_offering_repository(self):
        return self._course_offering_repository

    def build_course_section_repository(self):
        return self._course_section_repository

    def build_section_teacher_assignment_repository(self):
        return self._section_teacher_assignment_repository

    def build_academic_session_repository(self):
        return self._academic_session_repository

    def build_academic_term_repository(self):
        return self._academic_term_repository

    def build_academic_class_repository(self):
        return self._academic_class_repository

    def build_academic_subject_repository(self):
        return self._academic_subject_repository

    def build_teacher_subject_assignment_repository(self):
        return self._teacher_subject_assignment_repository

    def build_student_enrollment_repository(self):
        return self._student_enrollment_repository


    # -------------------------------------------------------------------
    # Service access
    # -------------------------------------------------------------------

    def build_talent_point_issuance_service(self):
        return self._talent_point_issuance_service

    def build_talent_point_transfer_service(self):
        return self._talent_point_transfer_service

    def build_service_act_service(self):
        return self._service_act_service
    def build_service_request_service(self):
        return self._service_request_service


    def build_verification_service(self):
        return self._verification_service

    def build_verification_decision_service(self):
        return self._verification_decision_service

    def build_service_act_verification_service(self):
        return self._service_act_verification_service

    def build_verification_workflow_service(self):
        return self._verification_workflow_service

    def build_dispute_service(self):
        return self._dispute_service

    def build_reputation_service(self):
        return self._reputation_service

    def build_reputation_profile_service(self):
        return self._reputation_profile_service

    def build_external_identity_service(self):
        return self._external_identity_service

    def build_authentication_service(self):
        return self._authentication_service

    def build_telegram_identity_service(self):
        return self._telegram_identity_service

    def build_telegram_channel_binding_service(self):
        return self._telegram_channel_binding_service

    def build_authorization_context_service(self):
        return self._authorization_context_service

    def build_authorization_service(self):
        return self._authorization_service

    def build_administration_context_service(self):
        return self._administration_context_service

    def build_rbac_provisioning_service(self):
        return self._rbac_provisioning_service
