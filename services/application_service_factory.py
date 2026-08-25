from repositories.service_act_repository import ServiceActRepository
from repositories.verification_repository import VerificationRepository
from repositories.talent_point_repository import TalentPointRepository
from repositories.dispute_repository import DisputeRepository
from repositories.reputation_repository import ReputationRepository

from services.service_act_service import ServiceActService
from services.verification_service import VerificationService
from services.verification_decision_service import VerificationDecisionService
from services.service_act_verification_service import ServiceActVerificationService
from services.verification_workflow_service import VerificationWorkflowService
from services.talent_point_issuance_service import TalentPointIssuanceService
from services.dispute_service import DisputeService
from services.reputation_service import ReputationService
from services.reputation_profile_service import ReputationProfileService


class ApplicationServiceFactory:
    """
    Composition root for KOSFintech application services.

    The factory constructs one coherent application service graph from
    one database connection.

    Repositories are constructed once.
    Services are constructed once.
    Composite services receive the already-constructed dependencies.

    Business logic remains inside services; dependency wiring remains here.
    """

    def __init__(self, connection):
        self.connection = connection

        # ---------------------------------------------------------------
        # Repository graph
        # ---------------------------------------------------------------

        self._service_act_repository = ServiceActRepository(connection)
        self._verification_repository = VerificationRepository(connection)
        self._talent_point_repository = TalentPointRepository(connection)
        self._dispute_repository = DisputeRepository(connection)
        self._reputation_repository = ReputationRepository(connection)

        # ---------------------------------------------------------------
        # Core service graph
        # ---------------------------------------------------------------

        self._service_act_service = ServiceActService(
            self._service_act_repository
        )

        self._verification_service = VerificationService(
            repository=self._verification_repository,
            service_act_repository=self._service_act_repository,
        )

        self._verification_decision_service = VerificationDecisionService(
            self._verification_repository
        )

        self._service_act_verification_service = (
            ServiceActVerificationService(
                verification_decision_service=(
                    self._verification_decision_service
                ),
                service_act_service=self._service_act_service,
            )
        )

        self._verification_workflow_service = VerificationWorkflowService(
            verification_service=self._verification_service,
            service_act_verification_service=(
                self._service_act_verification_service
            ),
        )

        self._talent_point_issuance_service = (
            TalentPointIssuanceService(
                self._talent_point_repository
            )
        )

        self._dispute_service = DisputeService(
            repository=self._dispute_repository,
            service_act_repository=self._service_act_repository,
        )

        self._reputation_service = ReputationService(
            repository=self._reputation_repository,
            service_act_repository=self._service_act_repository,
        )

        self._reputation_profile_service = ReputationProfileService(
            repository=self._reputation_repository,
        )

    # -------------------------------------------------------------------
    # Repository access
    # -------------------------------------------------------------------

    def build_service_act_repository(self):
        return self._service_act_repository

    def build_verification_repository(self):
        return self._verification_repository

    def build_talent_point_repository(self):
        return self._talent_point_repository

    def build_dispute_repository(self):
        return self._dispute_repository

    def build_reputation_repository(self):
        return self._reputation_repository

    # -------------------------------------------------------------------
    # Service access
    # -------------------------------------------------------------------

    def build_talent_point_issuance_service(self):
        return self._talent_point_issuance_service

    def build_service_act_service(self):
        return self._service_act_service

    def build_verification_service(self):
        return self._verification_service

    def build_verification_decision_service(self):
        return self._verification_decision_service

    def build_service_act_verification_service(self):
        return self._service_act_verification_service

    def build_verification_workflow_service(self):
        return self._verification_workflow_service

    def build_dispute_service(self):
        return self._dispute_service

    def build_reputation_service(self):
        return self._reputation_service

    def build_reputation_profile_service(self):
        return self._reputation_profile_service
