import database

from repositories.session_teacher_preacher_assignment_repository import (
    SessionTeacherPreacherAssignmentRepository,
)
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices
from services.session_teacher_preacher_assignment_service import (
    SessionTeacherPreacherAssignmentService,
)


def test_application_service_exposes_session_teacher_preacher_assignment():
    database.init_db()
    connection = database.get_connection()

    try:
        factory = ApplicationServiceFactory(connection)
        application_services = ApplicationServices(factory)

        service = application_services.session_teacher_preacher_assignment(
            tenant_id="tenant-1",
        )

        assert isinstance(
            service,
            SessionTeacherPreacherAssignmentService,
        )
        assert isinstance(
            service.repository,
            SessionTeacherPreacherAssignmentRepository,
        )
        assert service.tenant_id == "tenant-1"
        assert service.connection is connection
    finally:
        connection.close()
