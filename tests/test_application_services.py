import database
import pytest

from services.application_service_factory import ApplicationServiceFactory
from services.authentication_service import AuthenticationService
from services.application_services import ApplicationServices
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from services.service_act_service import ServiceActService
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
