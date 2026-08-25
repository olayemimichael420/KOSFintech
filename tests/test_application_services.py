import database
import pytest

from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices
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
