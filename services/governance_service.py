from datetime import datetime, timezone

from audit import audit_event
from policies.governance_policy import GovernanceAction, evaluate
from models.governance_proposal import (
    GovernanceProposal,
    GovernanceProposalStatus,
)
from models.governance_vote import (
    GovernanceVote,
    GovernanceVoteChoice,
)


class GovernanceService:
    """
    Application service for community governance proposals and voting.

    Initial governance rules:
    - Proposals belong to a tenant.
    - The proposer must be an active tenant user.
    - New proposals start as DRAFT.
    - Only DRAFT proposals may be opened.
    - Only OPEN proposals may receive votes.
    - Only OPEN proposals may be closed or cancelled.
    - A user may cast only one vote per proposal.
    - Governance operations are transactionally atomic.
    - Successful consequential operations emit audit events.
    - Governance does not directly mutate Talent Point balances.
    """

    def __init__(
        self,
        proposal_repository,
        vote_repository,
    ):
        self.proposal_repository = proposal_repository
        self.vote_repository = vote_repository

    def create_proposal(
        self,
        tenant_id: str,
        proposer_user_id: int,
        title: str,
        description: str,
    ) -> GovernanceProposal:
        if not title or not title.strip():
            raise ValueError("proposal title is required")

        if not description or not description.strip():
            raise ValueError("proposal description is required")

        self._require_governance_action(
            GovernanceAction.CREATE_PROPOSAL,
            tenant_id,
            proposer_user_id,
        )

        proposal = GovernanceProposal(
            id=None,
            tenant_id=tenant_id,
            proposer_user_id=proposer_user_id,
            title=title.strip(),
            description=description.strip(),
            status=GovernanceProposalStatus.DRAFT,
        )

        connection = self.proposal_repository.connection

        try:
            connection.execute("BEGIN")

            proposal = self.proposal_repository.create(
                proposal,
                commit=False,
            )

            audit_event(
                event_type="governance_proposal_created",
                actor_id=proposer_user_id,
                tenant_id=tenant_id,
                action="create_governance_proposal",
                metadata={
                    "proposal_id": proposal.id,
                    "title": proposal.title,
                },
                connection=connection,
            )

            connection.commit()
            return proposal

        except Exception:
            connection.rollback()
            raise

    def open_proposal(
        self,
        tenant_id: str,
        proposal_id: int,
        actor_user_id: int,
    ) -> GovernanceProposal:
        proposal = self._get_proposal(
            tenant_id,
            proposal_id,
        )

        self._require_governance_action(
            GovernanceAction.OPEN_PROPOSAL,
            tenant_id,
            actor_user_id,
        )

        if proposal.status != GovernanceProposalStatus.DRAFT:
            raise ValueError(
                "only draft proposals can be opened"
            )

        now = datetime.now(timezone.utc).isoformat()

        connection = self.proposal_repository.connection

        try:
            connection.execute("BEGIN")

            connection.execute(
                """
                UPDATE governance_proposals
                SET
                    status = ?,
                    opened_at = ?
                WHERE tenant_id = ?
                  AND id = ?
                """,
                (
                    GovernanceProposalStatus.OPEN.value,
                    now,
                    tenant_id,
                    proposal_id,
                ),
            )

            opened = self._get_proposal(
                tenant_id,
                proposal_id,
            )

            audit_event(
                event_type="governance_proposal_opened",
                actor_id=actor_user_id,
                tenant_id=tenant_id,
                action="open_governance_proposal",
                metadata={
                    "proposal_id": opened.id,
                },
                connection=connection,
            )

            connection.commit()
            return opened

        except Exception:
            connection.rollback()
            raise

    def cast_vote(
        self,
        tenant_id: str,
        proposal_id: int,
        voter_user_id: int,
        choice: GovernanceVoteChoice,
    ) -> GovernanceVote:
        if not isinstance(choice, GovernanceVoteChoice):
            try:
                choice = GovernanceVoteChoice(choice)
            except (TypeError, ValueError):
                raise ValueError("invalid governance vote choice")

        proposal = self._get_proposal(
            tenant_id,
            proposal_id,
        )

        self._require_governance_action(
            GovernanceAction.CAST_VOTE,
            tenant_id,
            voter_user_id,
        )

        if proposal.status != GovernanceProposalStatus.OPEN:
            raise ValueError(
                "only open proposals can receive votes"
            )

        existing = self.vote_repository.get_by_voter(
            tenant_id,
            proposal_id,
            voter_user_id,
        )

        if existing is not None:
            raise ValueError(
                "user has already voted on this proposal"
            )

        vote = GovernanceVote(
            id=None,
            tenant_id=tenant_id,
            proposal_id=proposal_id,
            voter_user_id=voter_user_id,
            choice=choice,
        )

        connection = self.vote_repository.connection

        try:
            connection.execute("BEGIN")

            vote = self.vote_repository.create(
                vote,
                commit=False,
            )

            audit_event(
                event_type="governance_vote_cast",
                actor_id=voter_user_id,
                tenant_id=tenant_id,
                action="cast_governance_vote",
                metadata={
                    "proposal_id": proposal_id,
                    "vote_id": vote.id,
                    "choice": choice.value,
                },
                connection=connection,
            )

            connection.commit()
            return vote

        except Exception:
            connection.rollback()
            raise

    def close_proposal(
        self,
        tenant_id: str,
        proposal_id: int,
        actor_user_id: int,
    ) -> GovernanceProposal:
        return self._finish_proposal(
            tenant_id=tenant_id,
            proposal_id=proposal_id,
            actor_user_id=actor_user_id,
            status=GovernanceProposalStatus.CLOSED,
            event_type="governance_proposal_closed",
            action="close_governance_proposal",
        )

    def cancel_proposal(
        self,
        tenant_id: str,
        proposal_id: int,
        actor_user_id: int,
    ) -> GovernanceProposal:
        return self._finish_proposal(
            tenant_id=tenant_id,
            proposal_id=proposal_id,
            actor_user_id=actor_user_id,
            status=GovernanceProposalStatus.CANCELLED,
            event_type="governance_proposal_cancelled",
            action="cancel_governance_proposal",
        )

    def _require_governance_action(
        self,
        action: GovernanceAction,
        tenant_id: str,
        user_id: int,
    ) -> None:
        user = self.proposal_repository.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        is_active_user = (
            user is not None
            and user["status"] == "active"
        )

        same_tenant = (
            user is not None
            and user["tenant_id"] == tenant_id
        )

        allowed, reason = evaluate(
            action=action,
            is_active_user=is_active_user,
            same_tenant=same_tenant,
        )

        if not allowed:
            raise ValueError(reason)

    def _finish_proposal(
        self,
        tenant_id,
        proposal_id,
        actor_user_id,
        status,
        event_type,
        action,
    ):
        proposal = self._get_proposal(
            tenant_id,
            proposal_id,
        )

        self._require_governance_action(
            GovernanceAction.CLOSE_PROPOSAL
            if status == GovernanceProposalStatus.CLOSED
            else GovernanceAction.CANCEL_PROPOSAL,
            tenant_id,
            actor_user_id,
        )

        if proposal.status != GovernanceProposalStatus.OPEN:
            raise ValueError(
                "only open proposals can be closed or cancelled"
            )

        now = datetime.now(timezone.utc).isoformat()

        connection = self.proposal_repository.connection

        try:
            connection.execute("BEGIN")

            connection.execute(
                """
                UPDATE governance_proposals
                SET
                    status = ?,
                    closed_at = ?
                WHERE tenant_id = ?
                  AND id = ?
                """,
                (
                    status.value,
                    now,
                    tenant_id,
                    proposal_id,
                ),
            )

            finished = self._get_proposal(
                tenant_id,
                proposal_id,
            )

            audit_event(
                event_type=event_type,
                actor_id=actor_user_id,
                tenant_id=tenant_id,
                action=action,
                metadata={
                    "proposal_id": finished.id,
                },
                connection=connection,
            )

            connection.commit()
            return finished

        except Exception:
            connection.rollback()
            raise

    def _get_proposal(
        self,
        tenant_id: str,
        proposal_id: int,
    ) -> GovernanceProposal:
        proposal = self.proposal_repository.get(
            tenant_id,
            proposal_id,
        )

        if proposal is None:
            raise ValueError("governance proposal not found")

        return proposal

    def _require_active_user(
        self,
        tenant_id: str,
        user_id: int,
    ) -> None:
        row = self.proposal_repository.connection.execute(
            """
            SELECT tenant_id, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            raise ValueError("user not found")

        if row["tenant_id"] != tenant_id:
            raise ValueError("user tenant mismatch")

        if row["status"] != "active":
            raise ValueError("user is inactive")
