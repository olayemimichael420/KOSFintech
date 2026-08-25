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

    This class constructs real repositories and services from one
    database connection. Business logic remains inside the services;
    dependency wiring remains here.
    """

    def __init__(self, connection):
        self.connection = connection

    def build_service_act_repository(self):
        return ServiceActRepository(self.connection)

    def build_verification_repository(self):
        return VerificationRepository(self.connection)

    def build_talent_point_repository(self):
        return TalentPointRepository(self.connection)

    def build_dispute_repository(self):
        return DisputeRepository(self.connection)

    def build_reputation_repository(self):
        return ReputationRepository(self.connection)

    def build_talent_point_issuance_service(self):
        return TalentPointIssuanceService(
            self.build_talent_point_repository()
        )

    def build_service_act_service(self):
        return ServiceActService(
            self.build_service_act_repository()
        )

    def build_verification_service(self):
        return VerificationService(
            repository=self.build_verification_repository(),
            service_act_repository=self.build_service_act_repository(),
        )

    def build_verification_decision_service(self):
        return VerificationDecisionService(
            self.build_verification_repository()
        )

    def build_service_act_verification_service(self):
        return ServiceActVerificationService(
            verification_decision_service=self.build_verification_decision_service(),
            service_act_service=self.build_service_act_service(),
        )

    def build_verification_workflow_service(self):
        return VerificationWorkflowService(
            verification_service=self.build_verification_service(),
            service_act_verification_service=(
                self.build_service_act_verification_service()
            ),
        )

    def build_dispute_service(self):
        return DisputeService(
            repository=self.build_dispute_repository(),
            service_act_repository=self.build_service_act_repository(),
        )

    def build_reputation_service(self):
        return ReputationService(
            repository=self.build_reputation_repository(),
            service_act_repository=self.build_service_act_repository(),
        )

    def build_reputation_profile_service(self):
        return ReputationProfileService(
            repository=self.build_reputation_repository(),
        )
