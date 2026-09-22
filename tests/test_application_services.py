import database
import pytest

from services.application_service_factory import ApplicationServiceFactory
from services.authentication_service import AuthenticationService
from services.application_services import ApplicationServices
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from services.service_act_service import ServiceActService
from services.service_request_service import ServiceRequestService
from services.verification_service import VerificationService
from services.verification_workflow_service import VerificationWorkflowService


@pytest.fixture
def connection(tmp_path, monkeypatch):
    db_path = tmp_path / "application_services.db"
    monkeypatch.setenv("DB_FILE", str(db_path))

    database.init_db()
    connection = database.get_connection()

    try:
        yield connection
    finally:
        connection.close()


def test_application_services_exposes_church_activity(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    church_activity = services.church_activity("tenant-cmos")

    from services.church_activity_service import ChurchActivityService

    assert isinstance(church_activity, ChurchActivityService)
    assert (
        church_activity.repository
        is services.factory.build_church_activity_repository()
    )


def test_application_services_exposes_verification_workflow(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    assert isinstance(
        services.verification_workflow,
        VerificationWorkflowService,
    )


def test_application_services_exposes_verification(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    assert isinstance(
        services.verification,
        VerificationService,
    )


def test_application_services_exposes_service_act(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    assert isinstance(
        services.service_act,
        ServiceActService,
    )


def test_application_services_exposes_service_request(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    assert isinstance(
        services.service_request,
        ServiceRequestService,
    )


def test_application_services_returns_same_service_instances(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    assert services.verification_workflow is services.verification_workflow
    assert services.verification is services.verification
    assert services.service_act is services.service_act
    assert services.talent_point_issuance is services.talent_point_issuance
    assert services.dispute is services.dispute
    assert services.reputation is services.reputation
    assert services.reputation_profile is services.reputation_profile


def test_application_services_preserves_shared_dependency_graph(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    workflow = services.verification_workflow
    verification = services.verification
    service_act = services.service_act

    assert workflow.verification_service is verification

    assert (
        workflow.service_act_verification_service.service_act_service
        is service_act
    )

    assert (
        workflow.service_act_verification_service.verification_decision_service
        is services.factory.build_verification_decision_service()
    )

    assert (
        verification.service_act_repository
        is service_act.repository
    )

    assert (
        services.dispute.service_act_repository
        is service_act.repository
    )

    assert (
        services.reputation.service_act_repository
        is service_act.repository
    )


def test_application_services_factory_returns_same_instances(connection):
    factory = ApplicationServiceFactory(connection)

    assert (
        factory.build_service_act_service()
        is factory.build_service_act_service()
    )

    assert (
        factory.build_verification_service()
        is factory.build_verification_service()
    )

    assert (
        factory.build_verification_decision_service()
        is factory.build_verification_decision_service()
    )

    assert (
        factory.build_service_act_verification_service()
        is factory.build_service_act_verification_service()
    )

    assert (
        factory.build_verification_workflow_service()
        is factory.build_verification_workflow_service()
    )

    assert (
        factory.build_talent_point_issuance_service()
        is factory.build_talent_point_issuance_service()
    )

    assert (
        factory.build_dispute_service()
        is factory.build_dispute_service()
    )

    assert (
        factory.build_reputation_service()
        is factory.build_reputation_service()
    )

    assert (
        factory.build_reputation_profile_service()
        is factory.build_reputation_profile_service()
    )


def test_application_services_builds_context_bound_attendance_service(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    attendance = services.attendance(
        tenant_id="school-001",
        user_id=1,
    )

    assert isinstance(attendance, AttendanceService)
    assert attendance.tenant_id == "school-001"
    assert attendance.user_id == 1
    assert attendance.repository is services.factory.build_attendance_repository()
    assert attendance.connection is connection


def test_application_services_builds_context_bound_student_service(connection):
    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    student = services.student(
        tenant_id="school-001",
        user_id=1,
    )

    assert isinstance(student, StudentService)
    assert student.tenant_id == "school-001"
    assert student.user_id == 1
    assert student.repository is services.factory.build_student_repository()
    assert student.connection is connection


def test_application_services_builds_context_bound_teacher_service(connection):
    from services.teacher_service import TeacherService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    teacher = services.teacher(
        tenant_id="school-001",
        user_id=1,
    )

    assert isinstance(teacher, TeacherService)
    assert teacher.tenant_id == "school-001"
    assert teacher.user_id == 1
    assert teacher.repository is services.factory.build_teacher_repository()
    assert teacher.connection is connection



def test_application_services_builds_context_bound_parent_service(connection):
    from services.parent_service import ParentService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    parent = services.parent(
        tenant_id="school-001",
        user_id=1,
    )

    assert isinstance(parent, ParentService)
    assert parent.tenant_id == "school-001"
    assert parent.user_id == 1
    assert parent.repository is services.factory.build_parent_repository()
    assert parent.connection is connection


def test_application_services_builds_context_bound_parent_student_service(connection):
    from services.parent_student_service import ParentStudentService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    parent_student = services.parent_student(
        tenant_id="school-001",
        user_id=1,
    )

    assert isinstance(parent_student, ParentStudentService)
    assert parent_student.tenant_id == "school-001"
    assert parent_student.user_id == 1
    assert parent_student.repository is services.factory.build_parent_student_repository()
    assert parent_student.connection is connection


def test_application_services_exposes_shared_authentication_service(connection):
    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert isinstance(services.authentication, AuthenticationService)
    assert services.authentication is factory.build_authentication_service()
    assert services.authentication.connection is connection

from services.administration_provisioning_service import (
    AdministrationProvisioningService,
)


def test_application_services_exposes_teaching_session(connection):
    from services.teaching_session_service import TeachingSessionService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_session = services.teaching_session("tenant-cmos")

    assert isinstance(teaching_session, TeachingSessionService)
    assert (
        teaching_session.repository
        is factory.build_teaching_session_repository()
    )
    assert teaching_session.tenant_id == "tenant-cmos"


def test_application_services_exposes_person_identity(connection):
    from services.person_identity_service import PersonIdentityService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert isinstance(services.person_identity, PersonIdentityService)
    assert services.person_identity is factory.build_person_identity_service()
    assert services.person_identity is services.person_identity


def test_application_services_exposes_administration_provisioning(connection):
    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert isinstance(
        services.administration_provisioning,
        AdministrationProvisioningService,
    )
    assert (
        services.administration_provisioning
        is factory.build_administration_provisioning_service()
    )

from services.tenant_service import TenantService


def test_application_services_exposes_tenant(connection):
    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert isinstance(
        services.tenant,
        TenantService,
    )
    assert (
        services.tenant
        is factory.build_tenant_service()
    )


def test_application_services_returns_same_tenant_service(connection):
    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert services.tenant is services.tenant


def test_application_services_exposes_institution_anchor(connection):
    from services.institution_anchor_service import InstitutionAnchorService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    service = services.institution_anchor

    assert isinstance(service, InstitutionAnchorService)
    assert service.repository.connection is connection


def test_application_services_exposes_service_binding(connection):
    from services.service_binding_service import ServiceBindingService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    service = services.service_binding

    assert isinstance(service, ServiceBindingService)
    assert service.repository.connection is connection


def test_application_services_exposes_teaching_series(connection):
    from services.teaching_series_service import TeachingSeriesService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_series = services.teaching_series("tenant-cmos")

    assert isinstance(teaching_series, TeachingSeriesService)
    assert (
        teaching_series.repository
        is factory.build_teaching_series_repository()
    )
    assert (
        teaching_series.session_repository
        is factory.build_teaching_session_repository()
    )
    assert teaching_series.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_content(connection):
    from services.teaching_content_service import TeachingContentService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_content = services.teaching_content("tenant-cmos")

    assert isinstance(teaching_content, TeachingContentService)
    assert (
        teaching_content.repository
        is factory.build_teaching_content_repository()
    )
    assert (
        teaching_content.focus_repository
        is factory.build_teaching_focus_repository()
    )
    assert teaching_content.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_subject(connection):
    from services.teaching_subject_service import TeachingSubjectService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_subject = services.teaching_subject("tenant-cmos")

    assert isinstance(teaching_subject, TeachingSubjectService)
    assert (
        teaching_subject.repository
        is factory.build_teaching_subject_repository()
    )
    assert teaching_subject.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_focus(connection):
    from services.teaching_focus_service import TeachingFocusService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_focus = services.teaching_focus("tenant-cmos")

    assert isinstance(teaching_focus, TeachingFocusService)
    assert (
        teaching_focus.repository
        is factory.build_teaching_focus_repository()
    )
    assert (
        teaching_focus.series_repository
        is factory.build_teaching_series_repository()
    )
    assert teaching_focus.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_focus(connection):
    from services.teaching_focus_service import TeachingFocusService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teaching_focus = services.teaching_focus("tenant-cmos")

    assert isinstance(teaching_focus, TeachingFocusService)
    assert (
        teaching_focus.repository
        is factory.build_teaching_focus_repository()
    )
    assert (
        teaching_focus.series_repository
        is factory.build_teaching_series_repository()
    )
    assert teaching_focus.tenant_id == "tenant-cmos"


def test_application_services_exposes_teacher_preacher(connection):
    from services.teacher_preacher_service import TeacherPreacherService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    teacher_preacher = services.teacher_preacher("tenant-cmos")

    assert isinstance(teacher_preacher, TeacherPreacherService)
    assert (
        teacher_preacher.repository
        is factory.build_teacher_preacher_repository()
    )
    assert teacher_preacher.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_session_member(
    connection,
):
    from services.teaching_session_member_service import (
        TeachingSessionMemberService,
    )

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    member = services.teaching_session_member("tenant-cmos")

    assert isinstance(
        member,
        TeachingSessionMemberService,
    )
    assert (
        member.repository
        is factory.build_teaching_session_member_repository()
    )
    assert member.tenant_id == "tenant-cmos"


def test_application_services_exposes_teaching_session_attendance(
    connection,
):
    from services.teaching_session_attendance_service import (
        TeachingSessionAttendanceService,
    )

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    attendance = services.teaching_session_attendance("tenant-cmos")

    assert isinstance(
        attendance,
        TeachingSessionAttendanceService,
    )
    assert (
        attendance.repository
        is factory.build_teaching_session_attendance_repository()
    )
    assert attendance.tenant_id == "tenant-cmos"


def test_application_services_exposes_teacher_preacher_member(
    connection,
):
    from services.teacher_preacher_member_service import (
        TeacherPreacherMemberService,
    )

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    member = services.teacher_preacher_member("tenant-cmos")

    assert isinstance(
        member,
        TeacherPreacherMemberService,
    )
    assert (
        member.repository
        is factory.build_teacher_preacher_member_repository()
    )
    assert member.tenant_id == "tenant-cmos"


def test_application_services_exposes_teacher_preacher_subject_assignment(
    connection,
):
    from services.teacher_preacher_subject_assignment_service import (
        TeacherPreacherSubjectAssignmentService,
    )

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assignment = services.teacher_preacher_subject_assignment("tenant-cmos")

    assert isinstance(
        assignment,
        TeacherPreacherSubjectAssignmentService,
    )
    assert (
        assignment.repository
        is factory.build_teacher_preacher_subject_assignment_repository()
    )
    assert assignment.tenant_id == "tenant-cmos"

def test_application_services_exposes_learning_evidence(connection):
    from services.learning_evidence_service import LearningEvidenceService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    evidence = services.learning_evidence("tenant-cmos")

    assert isinstance(evidence, LearningEvidenceService)
    assert (
        evidence.repository
        is factory.build_learning_evidence_repository()
    )
    assert evidence.tenant_id == "tenant-cmos"


def test_application_services_exposes_assessment(connection):
    from services.assessment_service import AssessmentService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assessment = services.assessment("tenant-cmos")

    assert isinstance(assessment, AssessmentService)
    assert (
        assessment.repository
        is factory.build_assessment_repository()
    )
    assert assessment.tenant_id == "tenant-cmos"

def test_application_services_exposes_assessment_score(connection):
    from services.assessment_score_service import AssessmentScoreService

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    score = services.assessment_score("tenant-cmos")

    assert isinstance(score, AssessmentScoreService)
    assert (
        score.repository
        is factory.build_assessment_score_repository()
    )
    assert score.tenant_id == "tenant-cmos"


def test_application_services_exposes_cmos_assessment_outcome_workflow(
    connection,
):
    from services.cmos_assessment_outcome_workflow_service import (
        CMOSAssessmentOutcomeWorkflowService,
    )

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    workflow = services.cmos_assessment_outcome_workflow("tenant-cmos")

    assert isinstance(workflow, CMOSAssessmentOutcomeWorkflowService)
    assert workflow.assessment_score_service.tenant_id == "tenant-cmos"
    assert workflow.result_service.tenant_id == "tenant-cmos"


def test_application_services_builds_context_bound_result_service(connection):
    from services.result_service import ResultService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    result = services.result(
        tenant_id="tenant-cmos",
        user_id=1,
    )

    assert isinstance(result, ResultService)
    assert result.tenant_id == "tenant-cmos"
    assert result.user_id == 1
    assert result.repository is services.factory.build_result_repository()
    assert result.connection is connection


def test_application_services_builds_context_bound_progress_service(connection):
    from services.progress_service import ProgressService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    progress = services.progress(
        tenant_id="tenant-cmos",
        user_id=1,
    )

    assert isinstance(progress, ProgressService)
    assert progress.tenant_id == "tenant-cmos"
    assert progress.user_id == 1
    assert progress.repository is services.factory.build_progress_repository()
    assert progress.connection is connection


def test_application_services_builds_context_bound_membership_service(connection):
    from services.membership_service import MembershipService

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    membership = services.membership(
        tenant_id="tenant-cmos",
        user_id=1,
    )

    assert isinstance(membership, MembershipService)
    assert membership.tenant_id == "tenant-cmos"
    assert membership.user_id == 1
    assert membership.repository is services.factory.build_membership_repository()
    assert membership.connection is connection
