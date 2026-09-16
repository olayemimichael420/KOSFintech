import database
import pytest

from repositories.service_act_repository import ServiceActRepository
from repositories.service_request_repository import ServiceRequestRepository
from repositories.verification_repository import VerificationRepository
from services.application_service_factory import ApplicationServiceFactory
from services.authentication_service import AuthenticationService
from services.service_act_service import ServiceActService
from services.service_request_service import ServiceRequestService
from services.service_act_verification_service import ServiceActVerificationService
from services.verification_decision_service import VerificationDecisionService
from services.verification_service import VerificationService
from services.verification_workflow_service import VerificationWorkflowService


@pytest.fixture
def connection(tmp_path, monkeypatch):
    db_path = tmp_path / "factory_test.db"

    monkeypatch.setenv("DB_FILE", str(db_path))

    database.init_db()
    connection = database.get_connection()

    try:
        yield connection
    finally:
        connection.close()


def test_factory_builds_service_act_repository(connection):
    factory = ApplicationServiceFactory(connection)

    repository = factory.build_service_act_repository()

    assert isinstance(repository, ServiceActRepository)
    assert repository.connection is connection


def test_factory_builds_service_request_repository(connection):
    factory = ApplicationServiceFactory(connection)
    repository = factory.build_service_request_repository()

    assert isinstance(repository, ServiceRequestRepository)
    assert repository.connection is connection


def test_factory_builds_verification_repository(connection):
    factory = ApplicationServiceFactory(connection)

    repository = factory.build_verification_repository()

    assert isinstance(repository, VerificationRepository)
    assert repository.connection is connection


def test_factory_builds_service_act_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_service_act_service()

    assert isinstance(service, ServiceActService)
    assert isinstance(service.repository, ServiceActRepository)
    assert service.repository.connection is connection


def test_factory_builds_service_request_service(connection):
    factory = ApplicationServiceFactory(connection)
    service = factory.build_service_request_service()

    assert isinstance(service, ServiceRequestService)
    assert isinstance(service.repository, ServiceRequestRepository)
    assert service.repository.connection is connection


def test_factory_builds_verification_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_verification_service()

    assert isinstance(service, VerificationService)
    assert isinstance(service.repository, VerificationRepository)
    assert isinstance(service.service_act_repository, ServiceActRepository)


def test_factory_builds_verification_decision_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_verification_decision_service()

    assert isinstance(service, VerificationDecisionService)
    assert isinstance(
        service.verification_repository,
        VerificationRepository,
    )


def test_factory_builds_service_act_verification_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_service_act_verification_service()

    assert isinstance(service, ServiceActVerificationService)
    assert isinstance(
        service.verification_decision_service,
        VerificationDecisionService,
    )
    assert isinstance(
        service.service_act_service,
        ServiceActService,
    )


def test_factory_builds_verification_workflow_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_verification_workflow_service()

    assert isinstance(service, VerificationWorkflowService)
    assert isinstance(
        service.verification_service,
        VerificationService,
    )
    assert isinstance(
        service.service_act_verification_service,
        ServiceActVerificationService,
    )


def test_factory_builds_authentication_service(connection):
    factory = ApplicationServiceFactory(connection)
    service = factory.build_authentication_service()

    assert isinstance(service, AuthenticationService)
    assert service.connection is connection

from repositories.administration_repository import AdministrationRepository
from services.administration_provisioning_service import (
    AdministrationProvisioningService,
)


def test_factory_builds_administration_provisioning_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_administration_provisioning_service()

    assert isinstance(service, AdministrationProvisioningService)
    assert isinstance(service.repository, AdministrationRepository)
    assert service.repository.connection is connection


def test_factory_returns_same_administration_provisioning_service(connection):
    factory = ApplicationServiceFactory(connection)

    assert (
        factory.build_administration_provisioning_service()
        is factory.build_administration_provisioning_service()
    )

from repositories.tenant_repository import TenantRepository
from services.tenant_service import TenantService


def test_factory_builds_tenant_repository(connection):
    factory = ApplicationServiceFactory(connection)

    repository = factory.build_tenant_repository()

    assert isinstance(repository, TenantRepository)
    assert repository.connection is connection


def test_factory_builds_tenant_service(connection):
    factory = ApplicationServiceFactory(connection)

    service = factory.build_tenant_service()

    assert isinstance(service, TenantService)
    assert isinstance(service.repository, TenantRepository)
    assert service.repository.connection is connection


def test_factory_returns_same_tenant_service(connection):
    factory = ApplicationServiceFactory(connection)

    assert (
        factory.build_tenant_service()
        is factory.build_tenant_service()
    )
