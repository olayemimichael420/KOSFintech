from typing import Optional

from models.governance_proposal import (
    GovernanceProposal,
    GovernanceProposalStatus,
)


class GovernanceProposalRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        proposal: GovernanceProposal,
        commit: bool = True,
    ) -> GovernanceProposal:
        cursor = self.connection.execute(
            """
            INSERT INTO governance_proposals (
                tenant_id,
                proposer_user_id,
                title,
                description,
                status,
                opened_at,
                closed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal.tenant_id,
                proposal.proposer_user_id,
                proposal.title,
                proposal.description,
                proposal.status.value,
                proposal.opened_at,
                proposal.closed_at,
            ),
        )

        if commit:
            self.connection.commit()

        return self.get(
            proposal.tenant_id,
            cursor.lastrowid,
        )

    def get(
        self,
        tenant_id: str,
        proposal_id: int,
    ) -> Optional[GovernanceProposal]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposer_user_id,
                title,
                description,
                status,
                created_at,
                opened_at,
                closed_at
            FROM governance_proposals
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, proposal_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[GovernanceProposal]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposer_user_id,
                title,
                description,
                status,
                created_at,
                opened_at,
                closed_at
            FROM governance_proposals
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def list_by_proposer(
        self,
        tenant_id: str,
        proposer_user_id: int,
    ) -> list[GovernanceProposal]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposer_user_id,
                title,
                description,
                status,
                created_at,
                opened_at,
                closed_at
            FROM governance_proposals
            WHERE tenant_id = ?
              AND proposer_user_id = ?
            ORDER BY id
            """,
            (tenant_id, proposer_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> GovernanceProposal:
        return GovernanceProposal(
            id=row["id"],
            tenant_id=row["tenant_id"],
            proposer_user_id=row["proposer_user_id"],
            title=row["title"],
            description=row["description"],
            status=GovernanceProposalStatus(row["status"]),
            created_at=row["created_at"],
            opened_at=row["opened_at"],
            closed_at=row["closed_at"],
        )
