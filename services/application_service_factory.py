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
from repositories.administration_repository import AdministrationRepository
from repositories.tenant_repository import TenantRepository
from repositories.institution_anchor_repository import InstitutionAnchorRepository
from repositories.service_binding_repository import ServiceBindingRepository
from repositories.academic_session_repository import AcademicSessionRepository
from repositories.course_offering_repository import CourseOfferingRepository
from repositories.course_section_repository import CourseSectionRepository
from repositories.section_teacher_assignment_repository import SectionTeacherAssignmentRepository
from repositories.section_student_enrollment_repository import SectionStudentEnrollmentRepository
from repositories.academic_term_repository import AcademicTermRepository
from repositories.academic_class_repository import AcademicClassRepository
from repositories.academic_subject_repository import AcademicSubjectRepository
from repositories.membership_repository import MembershipRepository
from repositories.church_program_repository import ChurchProgramRepository
from repositories.church_activity_repository import ChurchActivityRepository
from repositories.teaching_session_repository import TeachingSessionRepository
from repositories.teaching_series_repository import TeachingSeriesRepository
from repositories.teaching_focus_repository import TeachingFocusRepository
from repositories.teaching_content_repository import TeachingContentRepository
from repositories.learning_evidence_repository import LearningEvidenceRepository
from repositories.assessment_repository import AssessmentRepository
from repositories.assessment_score_repository import AssessmentScoreRepository
from repositories.grade_repository import GradeRepository
from repositories.result_repository import ResultRepository
from repositories.progress_repository import ProgressRepository
from repositories.teaching_subject_repository import TeachingSubjectRepository
from repositories.person_repository import PersonRepository
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from repositories.teacher_preacher_member_repository import TeacherPreacherMemberRepository
from repositories.teaching_session_member_repository import TeachingSessionMemberRepository
from repositories.teaching_session_attendance_repository import TeachingSessionAttendanceRepository
from repositories.teacher_preacher_subject_assignment_repository import TeacherPreacherSubjectAssignmentRepository
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
from services.person_identity_service import PersonIdentityService
from services.permission_resolution_service import PermissionResolutionService
from services.authentication_service import AuthenticationService
from services.authorization_context_service import AuthorizationContextService
from services.authorization_service import AuthorizationService
from services.administration_context_service import AdministrationContextService
from services.administration_provisioning_service import AdministrationProvisioningService
from services.tenant_identity_generator import TenantIdentityGenerator
from services.tenant_service import TenantService
from services.institution_anchor_service import InstitutionAnchorService
from services.service_binding_service import ServiceBindingService
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
        self._administration_repository = AdministrationRepository(connection)
        self._tenant_repository = TenantRepository(connection)
        self._institution_anchor_repository = InstitutionAnchorRepository(connection)
        self._service_binding_repository = ServiceBindingRepository(connection)
        self._academic_session_repository = AcademicSessionRepository(connection)
        self._course_offering_repository = CourseOfferingRepository(connection)
        self._course_section_repository = CourseSectionRepository(connection)
        self._section_teacher_assignment_repository = SectionTeacherAssignmentRepository(connection)
        self._section_student_enrollment_repository = SectionStudentEnrollmentRepository(connection)
        self._academic_term_repository = AcademicTermRepository(connection)
        self._academic_class_repository = AcademicClassRepository(connection)
        self._academic_subject_repository = AcademicSubjectRepository(connection)
        self._membership_repository = MembershipRepository(connection)
        self._church_program_repository = ChurchProgramRepository(connection)
        self._church_activity_repository = ChurchActivityRepository(connection)
        self._teaching_session_repository = TeachingSessionRepository(connection)
        self._teaching_series_repository = TeachingSeriesRepository(connection)
        self._teaching_focus_repository = TeachingFocusRepository(connection)
        self._teaching_content_repository = TeachingContentRepository(connection)
        self._learning_evidence_repository = LearningEvidenceRepository(connection)
        self._assessment_repository = AssessmentRepository(connection)
        self._assessment_score_repository = AssessmentScoreRepository(connection)
        self._grade_repository = GradeRepository(connection)
        self._result_repository = ResultRepository(connection)
        self._progress_repository = ProgressRepository(connection)
        self._teaching_subject_repository = TeachingSubjectRepository(connection)
        self._person_repository = PersonRepository(connection)
        self._teacher_preacher_repository = TeacherPreacherRepository(connection)
        self._teacher_preacher_member_repository = TeacherPreacherMemberRepository(connection)
        self._teaching_session_member_repository = TeachingSessionMemberRepository(connection)
        self._teaching_session_attendance_repository = TeachingSessionAttendanceRepository(connection)
        self._teacher_preacher_subject_assignment_repository = TeacherPreacherSubjectAssignmentRepository(connection)
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
        self._administration_provisioning_service = (
            AdministrationProvisioningService(
                repository=self._administration_repository,
                tenant_repository=self._tenant_repository,
            )
        )
        self._tenant_identity_generator = TenantIdentityGenerator()
        self._tenant_service = TenantService(
            repository=self._tenant_repository,
            identity_generator=self._tenant_identity_generator,
        )
        self._institution_anchor_service = InstitutionAnchorService(
            repository=self._institution_anchor_repository,
        )
        self._service_binding_service = ServiceBindingService(
            repository=self._service_binding_repository,
            tenant_repository=self._tenant_repository,
            institution_anchor_repository=self._institution_anchor_repository,
        )

        # ---------------------------------------------------------------
        # Core service graph
        # ---------------------------------------------------------------

        self._person_identity_service = PersonIdentityService(
            repository=self._person_repository,
        )

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

    def build_section_student_enrollment_repository(self):
        return self._section_student_enrollment_repository

    def build_academic_session_repository(self):
        return self._academic_session_repository

    def build_academic_term_repository(self):
        return self._academic_term_repository

    def build_academic_class_repository(self):
        return self._academic_class_repository

    def build_academic_subject_repository(self):
        return self._academic_subject_repository

    def build_membership_repository(self):
        return self._membership_repository

    def build_person_repository(self):
        return self._person_repository

    def build_church_program_repository(self):
        return self._church_program_repository

    def build_church_activity_repository(self):
        return self._church_activity_repository

    def build_teaching_session_repository(self):
        return self._teaching_session_repository

    def build_teaching_series_repository(self):
        return self._teaching_series_repository

    def build_teaching_focus_repository(self):
        return self._teaching_focus_repository

    def build_teaching_content_repository(self):
        return self._teaching_content_repository

    def build_learning_evidence_repository(self):
        return self._learning_evidence_repository

    def build_assessment_repository(self):
        return self._assessment_repository

    def build_assessment_score_repository(self):
        return self._assessment_score_repository

    def build_grade_repository(self):
        return self._grade_repository

    def build_result_repository(self):
        return self._result_repository

    def build_progress_repository(self):
        return self._progress_repository

    def build_teaching_subject_repository(self):
        return self._teaching_subject_repository

    def build_teacher_preacher_repository(self):
        return self._teacher_preacher_repository

    def build_teacher_preacher_member_repository(self):
        return self._teacher_preacher_member_repository

    def build_teaching_session_member_repository(self):
        return self._teaching_session_member_repository

    def build_teaching_session_attendance_repository(self):
        return self._teaching_session_attendance_repository

    def build_teacher_preacher_subject_assignment_repository(self):
        return self._teacher_preacher_subject_assignment_repository

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

    def build_person_identity_service(self):
        return self._person_identity_service

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

    def build_administration_repository(self):
        return self._administration_repository

    def build_tenant_repository(self):
        return self._tenant_repository

    def build_institution_anchor_repository(self):
        return self._institution_anchor_repository

    def build_service_binding_repository(self):
        return self._service_binding_repository

    def build_administration_provisioning_service(self):
        return self._administration_provisioning_service

    def build_tenant_identity_generator(self):
        return self._tenant_identity_generator

    def build_tenant_service(self):
        return self._tenant_service

    def build_institution_anchor_service(self):
        return self._institution_anchor_service

    def build_service_binding_service(self):
        return self._service_binding_service
