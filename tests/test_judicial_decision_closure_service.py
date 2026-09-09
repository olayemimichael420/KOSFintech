import sqlite3

import pytest

from database import init_db
from services.judicial_actions_decisions_service import (
    JudicialActionsDecisionsService,
)
from services.judicial_decision_closure_service import (
    JudicialDecisionClosureService,
)


@pytest.fixture
def setup_j5e(tmp_path):
    db_path = tmp_path / "j5e.db"
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

    connection.executemany(
        """
        INSERT INTO users (
            id, tenant_id, name, email, role, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "tenant-001", "Judge", "judge@example.com", "member", "active"),
            (2, "tenant-001", "Other", "other@example.com", "member", "active"),
        ],
    )

    connection.execute(
        """
        INSERT INTO judicial_jurisdictions (
            id, tenant_id, jurisdiction_type, jurisdiction_scope,
            judicial_level, case_types, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            "service",
            "tenant-001",
            "primary",
            "service_dispute",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_appointments (
            id, tenant_id, candidate_user_id, jurisdiction_id,
            judicial_level, appointment_source, appointment_basis,
            qualification_record, appointed_by, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "primary",
            "test-source",
            "test-basis",
            "qualified",
            2,
            "appointed",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_authorities (
            id, tenant_id, user_id, authority_type, jurisdiction_id,
            judicial_level, appointment_id, conferral_id, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            "judge",
            1,
            "primary",
            1,
            1,
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_conferrals (
            id, tenant_id, appointment_id, authority_id,
            conferring_authority, conferral_instrument, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "test-conferring-authority",
            "test-instrument",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO service_acts (
            id, tenant_id, provider_user_id, recipient_user_id,
            title, description, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "Test service act",
            "Test description",
            "created",
        ),
    )

    connection.execute(
        """
        INSERT INTO disputes (
            id, tenant_id, service_act_id, initiator_user_id,
            initiator_role, reason, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "recipient",
            "Test dispute",
            "open",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_proceedings (
            id, tenant_id, dispute_id, jurisdiction_id,
            proceeding_type, status, opened_by_authority_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "service_dispute",
            "active",
            1,
        ),
    )

    connection.commit()
    return connection


def test_close_proceeding_from_decision_success(setup_j5e):
    actions_service = JudicialActionsDecisionsService(setup_j5e)

    decision = actions_service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Matter concluded.",
    )

    service = JudicialDecisionClosureService(setup_j5e)

    closed = service.close_proceeding_from_decision(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        closure_reason="Matter concluded.",
    )

    assert closed.id == 1
    assert closed.status.value == "closed"
    assert closed.closed_at is not None
    assert closed.closure_reason == "Matter concluded."

    persisted_decision = setup_j5e.execute(
        """
        SELECT proceeding_id, judicial_authority_id, decision_type, decision_reason
        FROM judicial_decisions
        WHERE id = ?
        """,
        (decision.id,),
    ).fetchone()

    assert persisted_decision["proceeding_id"] == 1
    assert persisted_decision["judicial_authority_id"] == 1
    assert persisted_decision["decision_type"] == "determination"
    assert persisted_decision["decision_reason"] == "Matter concluded."



def test_closure_does_not_mutate_dispute_or_service_act(setup_j5e):
    before_dispute = setup_j5e.execute(
        """
        SELECT status, reason
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    before_service_act = setup_j5e.execute(
        """
        SELECT status, title, description
        FROM service_acts
        WHERE id = 1
        """
    ).fetchone()

    actions_service = JudicialActionsDecisionsService(setup_j5e)

    decision = actions_service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Matter concluded.",
    )

    service = JudicialDecisionClosureService(setup_j5e)

    service.close_proceeding_from_decision(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        closure_reason="Matter concluded.",
    )

    after_dispute = setup_j5e.execute(
        """
        SELECT status, reason
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    after_service_act = setup_j5e.execute(
        """
        SELECT status, title, description
        FROM service_acts
        WHERE id = 1
        """
    ).fetchone()

    assert tuple(after_dispute) == tuple(before_dispute)
    assert tuple(after_service_act) == tuple(before_service_act)

def test_rejects_decision_for_different_proceeding(setup_j5e):
    setup_j5e.execute(
        """
        INSERT INTO judicial_proceedings (
            id, tenant_id, dispute_id, jurisdiction_id,
            proceeding_type, status, opened_by_authority_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            2,
            "tenant-001",
            1,
            1,
            "service_dispute",
            "active",
            1,
        ),
    )
    setup_j5e.commit()

    actions_service = JudicialActionsDecisionsService(setup_j5e)

    decision = actions_service.record_decision(
        user_id=1,
        proceeding_id=2,
        decision_type="determination",
        decision_reason="Different proceeding.",
    )

    service = JudicialDecisionClosureService(setup_j5e)

    with pytest.raises(ValueError, match="decision does not belong to proceeding"):
        service.close_proceeding_from_decision(
            user_id=1,
            proceeding_id=1,
            decision_id=decision.id,
            closure_reason="Attempted closure.",
        )

    status = setup_j5e.execute(
        """
        SELECT status
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()["status"]

    assert status == "active"


def test_rejects_missing_decision(setup_j5e):
    service = JudicialDecisionClosureService(setup_j5e)

    with pytest.raises(ValueError, match="judicial decision not found"):
        service.close_proceeding_from_decision(
            user_id=1,
            proceeding_id=1,
            decision_id=999,
            closure_reason="Attempted closure.",
        )

    status = setup_j5e.execute(
        """
        SELECT status
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()["status"]

    assert status == "active"


def test_requires_closure_reason(setup_j5e):
    service = JudicialDecisionClosureService(setup_j5e)

    with pytest.raises(ValueError, match="closure reason"):
        service.close_proceeding_from_decision(
            user_id=1,
            proceeding_id=1,
            decision_id=999,
            closure_reason="",
        )
