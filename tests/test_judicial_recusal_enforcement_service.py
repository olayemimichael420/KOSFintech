import sqlite3

import pytest

from database import init_db
from services.judicial_actions_decisions_service import (
    JudicialActionsDecisionsService,
)
from services.judicial_recusal_service import JudicialRecusalService
from models.judicial_recusal import JudicialRecusalScope


@pytest.fixture
def setup_j6d(tmp_path):
    db_path = tmp_path / "j6d.db"

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
            id,
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "tenant-001", "Judge One", "judge1@example.com", "member", "active"),
            (2, "tenant-001", "Judge Two", "judge2@example.com", "member", "active"),
            (3, "tenant-002", "Other Tenant", "other@example.com", "member", "active"),
        ],
    )

    connection.executemany(
        """
        INSERT INTO judicial_jurisdictions (
            id,
            tenant_id,
            jurisdiction_type,
            jurisdiction_scope,
            judicial_level,
            case_types,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                "service",
                "tenant-001",
                "primary",
                "service_dispute",
                "active",
            ),
            (
                2,
                "tenant-001",
                "service",
                "tenant-001-secondary",
                "primary",
                "service_dispute",
                "active",
            ),
            (
                3,
                "tenant-002",
                "service",
                "tenant-002",
                "primary",
                "service_dispute",
                "active",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO judicial_appointments (
            id,
            tenant_id,
            candidate_user_id,
            jurisdiction_id,
            judicial_level,
            appointment_source,
            appointment_basis,
            qualification_record,
            appointed_by,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                1,
                1,
                "primary",
                "test-source",
                "test-basis",
                "qualified",
                1,
                "appointed",
            ),
            (
                2,
                "tenant-001",
                2,
                2,
                "primary",
                "test-source",
                "test-basis",
                "qualified",
                1,
                "appointed",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO judicial_authorities (
            id,
            tenant_id,
            user_id,
            authority_type,
            jurisdiction_id,
            judicial_level,
            appointment_id,
            conferral_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
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
            (
                2,
                "tenant-001",
                2,
                "judge",
                2,
                "primary",
                2,
                2,
                "active",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                1,
                1,
                "test-conferring-authority",
                "test-instrument",
                "active",
            ),
            (
                2,
                "tenant-001",
                2,
                2,
                "test-conferring-authority",
                "test-instrument",
                "active",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO service_acts (
            id,
            tenant_id,
            provider_user_id,
            recipient_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                1,
                2,
                "Service One",
                "Service one description",
                "created",
            ),
            (
                2,
                "tenant-001",
                2,
                1,
                "Service Two",
                "Service two description",
                "created",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO disputes (
            id,
            tenant_id,
            service_act_id,
            initiator_user_id,
            initiator_role,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                1,
                2,
                "recipient",
                "Dispute one",
                "open",
            ),
            (
                2,
                "tenant-001",
                2,
                1,
                "provider",
                "Dispute two",
                "open",
            ),
        ],
    )

    connection.executemany(
        """
        INSERT INTO judicial_proceedings (
            id,
            tenant_id,
            dispute_id,
            jurisdiction_id,
            proceeding_type,
            status,
            opened_by_authority_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "tenant-001",
                1,
                1,
                "service_dispute",
                "active",
                1,
            ),
            (
                2,
                "tenant-001",
                2,
                2,
                "service_dispute",
                "active",
                2,
            ),
        ],
    )

    connection.commit()
    return connection


def _record_jurisdiction_recusal(connection):
    return JudicialRecusalService(connection).record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Test jurisdiction recusal",
    )


def _record_proceeding_recusal(connection):
    return JudicialRecusalService(connection).record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.PROCEEDING,
        proceeding_id=1,
        reason="Test proceeding recusal",
    )


@pytest.mark.parametrize(
    ("operation", "kwargs"),
    [
        (
            "record_action",
            {
                "action_type": "hearing",
                "action_details": "Hearing conducted.",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Decision recorded.",
            },
        ),
    ],
)
def test_no_active_recusal_allows_judicial_operation(
    setup_j6d,
    operation,
    kwargs,
):
    service = JudicialActionsDecisionsService(setup_j6d)

    result = getattr(service, operation)(
        user_id=1,
        proceeding_id=1,
        **kwargs,
    )

    assert result.id is not None


@pytest.mark.parametrize(
    ("operation", "kwargs"),
    [
        (
            "record_action",
            {
                "action_type": "hearing",
                "action_details": "Should be blocked.",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Should be blocked.",
            },
        ),
    ],
)
def test_active_jurisdiction_recusal_blocks_judicial_operation(
    setup_j6d,
    operation,
    kwargs,
):
    _record_jurisdiction_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    with pytest.raises(
        ValueError,
        match="judicial authority is recused from this jurisdiction",
    ):
        getattr(service, operation)(
            user_id=1,
            proceeding_id=1,
            **kwargs,
        )


@pytest.mark.parametrize(
    ("operation", "kwargs"),
    [
        (
            "record_action",
            {
                "action_type": "hearing",
                "action_details": "Should be blocked.",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Should be blocked.",
            },
        ),
    ],
)
def test_active_proceeding_recusal_blocks_judicial_operation(
    setup_j6d,
    operation,
    kwargs,
):
    _record_proceeding_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    with pytest.raises(
        ValueError,
        match="judicial authority is recused from this proceeding",
    ):
        getattr(service, operation)(
            user_id=1,
            proceeding_id=1,
            **kwargs,
        )


def test_resolved_recusal_does_not_block_operation(setup_j6d):
    recusal = _record_jurisdiction_recusal(setup_j6d)

    JudicialRecusalService(setup_j6d).resolve_recusal(
        user_id=1,
        recusal_id=recusal.id,
    )

    service = JudicialActionsDecisionsService(setup_j6d)

    result = service.record_action(
        user_id=1,
        proceeding_id=1,
        action_type="hearing",
        action_details="Allowed after resolution.",
    )

    assert result.id is not None


def test_proceeding_recusal_does_not_block_other_proceeding(setup_j6d):
    _record_proceeding_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    result = service.record_action(
        user_id=2,
        proceeding_id=2,
        action_type="hearing",
        action_details="Other proceeding.",
    )

    assert result.id is not None


def test_proceeding_recusal_does_not_block_other_authority(
    setup_j6d,
):
    _record_proceeding_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    result = service.record_decision(
        user_id=2,
        proceeding_id=2,
        decision_type="determination",
        decision_reason="Other authority.",
    )

    assert result.id is not None


def test_jurisdiction_recusal_does_not_block_other_authority(
    setup_j6d,
):
    _record_jurisdiction_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    result = service.record_action(
        user_id=2,
        proceeding_id=2,
        action_type="hearing",
        action_details="Other authority.",
    )

    assert result.id is not None


def test_blocked_judicial_operation_creates_no_action_or_decision(
    setup_j6d,
):
    _record_jurisdiction_recusal(setup_j6d)

    service = JudicialActionsDecisionsService(setup_j6d)

    with pytest.raises(ValueError):
        service.record_action(
            user_id=1,
            proceeding_id=1,
            action_type="hearing",
            action_details="Blocked.",
        )

    with pytest.raises(ValueError):
        service.record_decision(
            user_id=1,
            proceeding_id=1,
            decision_type="determination",
            decision_reason="Blocked.",
        )

    action_count = setup_j6d.execute(
        """
        SELECT COUNT(*)
        FROM judicial_actions
        WHERE tenant_id = 'tenant-001'
          AND proceeding_id = 1
        """
    ).fetchone()[0]

    decision_count = setup_j6d.execute(
        """
        SELECT COUNT(*)
        FROM judicial_decisions
        WHERE tenant_id = 'tenant-001'
          AND proceeding_id = 1
        """
    ).fetchone()[0]

    assert action_count == 0
    assert decision_count == 0


def test_foreign_tenant_recusal_does_not_block_operation(setup_j6d):
    recusal_service = JudicialRecusalService(setup_j6d)

    # Create a valid tenant-002 recusal context. The recusal must be
    # structurally valid because J6B intentionally enforces tenant-safe
    # foreign keys.
    setup_j6d.execute(
        """
        INSERT INTO judicial_appointments (
            id,
            tenant_id,
            candidate_user_id,
            jurisdiction_id,
            judicial_level,
            appointment_source,
            appointment_basis,
            qualification_record,
            appointed_by,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            3,
            "tenant-002",
            3,
            3,
            "primary",
            "test-source",
            "test-basis",
            "qualified",
            3,
            "appointed",
        ),
    )

    setup_j6d.execute(
        """
        INSERT INTO judicial_authorities (
            id,
            tenant_id,
            user_id,
            authority_type,
            jurisdiction_id,
            judicial_level,
            appointment_id,
            conferral_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            3,
            "tenant-002",
            3,
            "judge",
            3,
            "primary",
            3,
            3,
            "active",
        ),
    )

    setup_j6d.execute(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            3,
            "tenant-002",
            3,
            3,
            "test-conferring-authority",
            "test-instrument",
            "active",
        ),
    )

    setup_j6d.commit()

    recusal_service.record_recusal(
        user_id=3,
        judicial_authority_id=3,
        jurisdiction_id=3,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Foreign tenant recusal",
    )

    service = JudicialActionsDecisionsService(setup_j6d)

    result = service.record_action(
        user_id=1,
        proceeding_id=1,
        action_type="hearing",
        action_details="Tenant isolation test.",
    )

    assert result.id is not None


def test_recusal_gate_does_not_mutate_proceeding(
    setup_j6d,
):
    _record_jurisdiction_recusal(setup_j6d)

    before = setup_j6d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    service = JudicialActionsDecisionsService(setup_j6d)

    with pytest.raises(ValueError):
        service.record_decision(
            user_id=1,
            proceeding_id=1,
            decision_type="determination",
            decision_reason="Blocked.",
        )

    after = setup_j6d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    assert tuple(after) == tuple(before)
