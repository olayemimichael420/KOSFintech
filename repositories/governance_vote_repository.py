from typing import Optional

from models.governance_vote import (
    GovernanceVote,
    GovernanceVoteChoice,
)


class GovernanceVoteRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        vote: GovernanceVote,
        commit: bool = True,
    ) -> GovernanceVote:
        cursor = self.connection.execute(
            """
            INSERT INTO governance_votes (
                tenant_id,
                proposal_id,
                voter_user_id,
                choice
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                vote.tenant_id,
                vote.proposal_id,
                vote.voter_user_id,
                vote.choice.value,
            ),
        )

        if commit:
            self.connection.commit()

        return self.get(
            vote.tenant_id,
            cursor.lastrowid,
        )

    def get(
        self,
        tenant_id: str,
        vote_id: int,
    ) -> Optional[GovernanceVote]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposal_id,
                voter_user_id,
                choice,
                created_at
            FROM governance_votes
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, vote_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def get_by_voter(
        self,
        tenant_id: str,
        proposal_id: int,
        voter_user_id: int,
    ) -> Optional[GovernanceVote]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposal_id,
                voter_user_id,
                choice,
                created_at
            FROM governance_votes
            WHERE tenant_id = ?
              AND proposal_id = ?
              AND voter_user_id = ?
            """,
            (
                tenant_id,
                proposal_id,
                voter_user_id,
            ),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_proposal(
        self,
        tenant_id: str,
        proposal_id: int,
    ) -> list[GovernanceVote]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                proposal_id,
                voter_user_id,
                choice,
                created_at
            FROM governance_votes
            WHERE tenant_id = ?
              AND proposal_id = ?
            ORDER BY id
            """,
            (tenant_id, proposal_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> GovernanceVote:
        return GovernanceVote(
            id=row["id"],
            tenant_id=row["tenant_id"],
            proposal_id=row["proposal_id"],
            voter_user_id=row["voter_user_id"],
            choice=GovernanceVoteChoice(row["choice"]),
            created_at=row["created_at"],
        )
