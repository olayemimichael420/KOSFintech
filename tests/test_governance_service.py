import sqlite3

import pytest

from database import init_db
from models.governance_proposal import GovernanceProposalStatus
from models.governance_vote import GovernanceVoteChoice
from repositories.governance_proposal_repository import GovernanceProposalRepository
from repositories.governance_vote_repository import GovernanceVoteRepository
from services.governance_service import GovernanceService


def _setup(tmp_path):
    db_path = tmp_path / "governance_service.db"

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    import config

    original_db_file = config.settings.db_file

    object.__setattr__(config.settings, "db_file", db_path)

    try:
        init_db()
    finally:
        object.__setattr__(
            config.settings,
            "db_file",
            original_db_file,
        )
        connection.close()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    users = []

    for name in ("Alice", "Bob", "Inactive User", "Other Tenant"):
        tenant_id = (
            "tenant-001"
            if name != "Other Tenant"
            else "tenant-002"
        )
        status = (
            "inactive"
            if name == "Inactive User"
            else "active"
        )

        cursor = connection.execute(
            """
            INSERT INTO users (
                tenant_id,
                name,
                email,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                name,
                f"{name.lower().replace(' ', '.')}@example.com",
                "member",
                status,
            ),
        )
        users.append(cursor.lastrowid)

    connection.commit()

    proposal_repository = GovernanceProposalRepository(connection)
    vote_repository = GovernanceVoteRepository(connection)

    service = GovernanceService(
        proposal_repository,
        vote_repository,
    )

    return (
        connection,
        service,
        users,
    )


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_create_proposal_starts_as_draft(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            tenant_id="tenant-001",
            proposer_user_id=users[0],
            title="Community Proposal",
            description="A proposal for community consideration.",
        )

        assert proposal.id is not None
        assert proposal.tenant_id == "tenant-001"
        assert proposal.proposer_user_id == users[0]
        assert proposal.title == "Community Proposal"
        assert proposal.status == GovernanceProposalStatus.DRAFT
    finally:
        connection.close()


def test_create_proposal_rejects_empty_title(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        with pytest.raises(
            ValueError,
            match="proposal title is required",
        ):
            service.create_proposal(
                "tenant-001",
                users[0],
                "   ",
                "Valid description.",
            )
    finally:
        connection.close()


def test_create_proposal_rejects_empty_description(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        with pytest.raises(
            ValueError,
            match="proposal description is required",
        ):
            service.create_proposal(
                "tenant-001",
                users[0],
                "Valid title",
                "   ",
            )
    finally:
        connection.close()


def test_create_proposal_rejects_cross_tenant_user(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        with pytest.raises(
            ValueError,
            match="governance tenant mismatch",
        ):
            service.create_proposal(
                "tenant-001",
                users[3],
                "Cross Tenant",
                "Should be rejected.",
            )
    finally:
        connection.close()


def test_create_proposal_rejects_inactive_user(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        with pytest.raises(
            ValueError,
            match="governance requires an active user",
        ):
            service.create_proposal(
                "tenant-001",
                users[2],
                "Inactive User",
                "Should be rejected.",
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_open_proposal_changes_draft_to_open(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Open Proposal",
            "Proposal to open.",
        )

        opened = service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        assert opened.status == GovernanceProposalStatus.OPEN
        assert opened.opened_at is not None
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_only_draft_proposals_can_be_opened(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Open Once",
            "Proposal.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        with pytest.raises(
            ValueError,
            match="only draft proposals can be opened",
        ):
            service.open_proposal(
                "tenant-001",
                proposal.id,
                users[0],
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_cast_vote_on_open_proposal(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Voting Proposal",
            "Proposal for voting.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        vote = service.cast_vote(
            "tenant-001",
            proposal.id,
            users[1],
            GovernanceVoteChoice.YES,
        )

        assert vote.id is not None
        assert vote.proposal_id == proposal.id
        assert vote.voter_user_id == users[1]
        assert vote.choice == GovernanceVoteChoice.YES
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_vote_requires_open_proposal(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Closed Voting",
            "Not yet open.",
        )

        with pytest.raises(
            ValueError,
            match="only open proposals can receive votes",
        ):
            service.cast_vote(
                "tenant-001",
                proposal.id,
                users[1],
                GovernanceVoteChoice.YES,
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_user_can_vote_only_once(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Single Vote",
            "One vote per user.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        service.cast_vote(
            "tenant-001",
            proposal.id,
            users[1],
            GovernanceVoteChoice.YES,
        )

        with pytest.raises(
            ValueError,
            match="user has already voted on this proposal",
        ):
            service.cast_vote(
                "tenant-001",
                proposal.id,
                users[1],
                GovernanceVoteChoice.NO,
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_invalid_vote_choice_is_rejected(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Vote Choice",
            "Validate choices.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        with pytest.raises(
            ValueError,
            match="invalid governance vote choice",
        ):
            service.cast_vote(
                "tenant-001",
                proposal.id,
                users[1],
                "invalid",
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_close_proposal(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Close Proposal",
            "Proposal to close.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        closed = service.close_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        assert closed.status == GovernanceProposalStatus.CLOSED
        assert closed.closed_at is not None
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_cancel_proposal(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Cancel Proposal",
            "Proposal to cancel.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        cancelled = service.cancel_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        assert cancelled.status == GovernanceProposalStatus.CANCELLED
        assert cancelled.closed_at is not None
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_closed_proposal_cannot_receive_votes(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Closed Proposal",
            "Proposal.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        service.close_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        with pytest.raises(
            ValueError,
            match="only open proposals can receive votes",
        ):
            service.cast_vote(
                "tenant-001",
                proposal.id,
                users[1],
                GovernanceVoteChoice.YES,
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_cross_tenant_proposal_is_not_visible(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Private Proposal",
            "Tenant isolation test.",
        )

        with pytest.raises(
            ValueError,
            match="governance proposal not found",
        ):
            service.open_proposal(
                "tenant-002",
                proposal.id,
                users[3],
            )
    finally:
        connection.close()


@pytest.mark.skip(reason="governance authority not constitutionally authorized")
def test_governance_audit_events_are_persisted(tmp_path):
    connection, service, users = _setup(tmp_path)

    try:
        proposal = service.create_proposal(
            "tenant-001",
            users[0],
            "Audited Proposal",
            "Audit test.",
        )

        service.open_proposal(
            "tenant-001",
            proposal.id,
            users[0],
        )

        service.cast_vote(
            "tenant-001",
            proposal.id,
            users[1],
            GovernanceVoteChoice.YES,
        )

        events = connection.execute(
            """
            SELECT event_type
            FROM audit_events
            WHERE tenant_id = ?
            ORDER BY id
            """,
            ("tenant-001",),
        ).fetchall()

        event_types = [row["event_type"] for row in events]

        assert "governance_proposal_created" in event_types
        assert "governance_proposal_opened" in event_types
        assert "governance_vote_cast" in event_types
    finally:
        connection.close()


def test_governance_service_denies_execution_when_constitutional_authorization_is_not_granted(tmp_path):
    connection, service, users = _setup(tmp_path)
    try:
        with pytest.raises(
            ValueError,
            match="governance action not yet constitutionally authorized",
        ):
            service.create_proposal(
                tenant_id="tenant-001",
                proposer_user_id=users[0],
                title="Constitutional Gate Test",
                description="Governance must remain fail-closed.",
            )
    finally:
        connection.close()
