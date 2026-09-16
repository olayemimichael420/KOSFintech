from models.institution_anchor import InstitutionAnchor
from repositories.institution_anchor_repository import InstitutionAnchorRepository


class InstitutionAnchorService:
    def __init__(self, repository: InstitutionAnchorRepository):
        self.repository = repository

    def create(
        self,
        institution_type: str,
        name: str,
        provenance_reference: str,
        verification_status: str = "pending",
        status: str = "active",
    ) -> InstitutionAnchor:
        if verification_status not in {
            "pending",
            "verified",
            "rejected",
        }:
            raise ValueError("invalid verification status")

        if status not in {
            "active",
            "inactive",
        }:
            raise ValueError("invalid institution anchor status")

        anchor = InstitutionAnchor(
            id=None,
            institution_type=institution_type,
            name=name,
            provenance_reference=provenance_reference,
            verification_status=verification_status,
            status=status,
        )

        return self.repository.create(anchor)

    def get(self, anchor_id: int):
        return self.repository.get(anchor_id)

    def list_active(self) -> list[InstitutionAnchor]:
        return self.repository.list_active()
