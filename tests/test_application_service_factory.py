import database
import pytest

from repositories.service_act_repository import ServiceActRepository
from repositories.verification_repository import VerificationRepository
from services.application_service_factory import ApplicationServiceFactory
from services.service_act_service import ServiceActService
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
