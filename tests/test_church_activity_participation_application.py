import sqlite3

import database

from repositories.church_activity_participation_repository import (
    ChurchActivityParticipationRepository,
)
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices
from services.church_activity_participation_service import (
    ChurchActivityParticipationService,
)


def test_application_service_exposes_church_activity_participation():
    database.init_db()
    connection = database.get_connection()

    factory = ApplicationServiceFactory(connection)
    application_services = ApplicationServices(factory)

    service = application_services.church_activity_participation(
        tenant_id="tenant-1",
    )

    assert isinstance(service, ChurchActivityParticipationService)
    assert isinstance(
        service.repository,
        ChurchActivityParticipationRepository,
    )
    assert service.tenant_id == "tenant-1"
    assert service.connection is connection
