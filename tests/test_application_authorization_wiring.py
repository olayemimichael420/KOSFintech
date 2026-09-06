from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices
from services.authorization_context_service import AuthorizationContextService
from services.authorization_service import AuthorizationService


def test_application_services_exposes_factory_authorization_services():
    import sqlite3

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    factory = ApplicationServiceFactory(connection)
    services = ApplicationServices(factory)

    assert isinstance(
        services.authorization_context,
        AuthorizationContextService,
    )
    assert isinstance(
        services.authorization,
        AuthorizationService,
    )

    assert services.authorization_context is (
        factory.build_authorization_context_service()
    )
    assert services.authorization is (
        factory.build_authorization_service()
    )
