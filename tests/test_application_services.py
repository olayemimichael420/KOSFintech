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
