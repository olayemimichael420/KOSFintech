from services.application_service_factory import ApplicationServiceFactory


class ApplicationServices:
    """
    Application-scoped service container.

    The container owns the application service graph for one database
    connection. Telegram handlers should obtain application services
    through this boundary rather than constructing repositories/services
    directly.
    """

    def __init__(self, factory: ApplicationServiceFactory):
        self.factory = factory

    @property
    def verification_workflow(self):
        return self.factory.build_verification_workflow_service()

    @property
    def verification(self):
        return self.factory.build_verification_service()

    @property
    def service_act(self):
        return self.factory.build_service_act_service()

    @property
    def talent_point_issuance(self):
        return self.factory.build_talent_point_issuance_service()
