import pytest

from services.judicial_actions_decisions_service import (
    JudicialActionsDecisionsService,
)


def test_record_action_success(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    action = service.record_action(
        user_id=1,
        proceeding_id=1,
        action_type="hearing",
        action_details="Hearing conducted.",
    )

    assert action.id is not None
    assert action.tenant_id == "tenant-001"
    assert action.proceeding_id == 1
    assert action.judicial_authority_id == 1
    assert action.action_type == "hearing"
    assert action.action_details == "Hearing conducted."
    assert action.acted_at is not None


def test_record_decision_success(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    decision = service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Evidence reviewed and determination recorded.",
    )

    assert decision.id is not None
    assert decision.tenant_id == "tenant-001"
    assert decision.proceeding_id == 1
    assert decision.judicial_authority_id == 1
    assert decision.decision_type == "determination"
    assert decision.decision_reason == (
        "Evidence reviewed and determination recorded."
    )
    assert decision.decided_at is not None


@pytest.mark.parametrize(
    ("operation", "kwargs"),
    [
        (
            "record_action",
            {
                "action_type": "hearing",
                "action_details": "Details",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Reason",
            },
        ),
    ],
)
def test_requires_active_authority(
    setup_j5d,
    operation,
    kwargs,
):
    setup_j5d.execute(
        """
        UPDATE judicial_authorities
        SET status = 'suspended'
        WHERE id = 1
        """
    )
    setup_j5d.commit()

    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(ValueError, match="no active judicial authority"):
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
                "action_details": "Details",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Reason",
            },
        ),
    ],
)
def test_requires_active_proceeding(
    setup_j5d,
    operation,
    kwargs,
):
    setup_j5d.execute(
        """
        UPDATE judicial_proceedings
        SET status = 'closed'
        WHERE id = 1
        """
    )
    setup_j5d.commit()

    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(
        ValueError,
        match="only active judicial proceedings",
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
                "action_details": "Details",
            },
        ),
        (
            "record_decision",
            {
                "decision_type": "determination",
                "decision_reason": "Reason",
            },
        ),
    ],
)
def test_requires_existing_proceeding(
    setup_j5d,
    operation,
    kwargs,
):
    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(ValueError, match="judicial proceeding not found"):
        getattr(service, operation)(
            user_id=1,
            proceeding_id=999,
            **kwargs,
        )


def test_rejects_empty_action_fields(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(ValueError, match="action type is required"):
        service.record_action(
            user_id=1,
            proceeding_id=1,
            action_type=" ",
            action_details="Details",
        )

    with pytest.raises(ValueError, match="action details is required"):
        service.record_action(
            user_id=1,
            proceeding_id=1,
            action_type="hearing",
            action_details=" ",
        )


def test_rejects_empty_decision_fields(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(ValueError, match="decision type is required"):
        service.record_decision(
            user_id=1,
            proceeding_id=1,
            decision_type=" ",
            decision_reason="Reason",
        )

    with pytest.raises(ValueError, match="decision reason is required"):
        service.record_decision(
            user_id=1,
            proceeding_id=1,
            decision_type="determination",
            decision_reason=" ",
        )


def test_jurisdiction_mismatch_is_rejected(setup_j5d):
    setup_j5d.execute(
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
        (
            3,
            "tenant-001",
            "service",
            "tenant-001-secondary",
            "primary",
            "service_dispute",
            "active",
        ),
    )

    setup_j5d.execute(
        """
        UPDATE judicial_proceedings
        SET jurisdiction_id = 3
        WHERE id = 1
        """
    )
    setup_j5d.commit()

    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(
        ValueError,
        match="judicial authority jurisdiction mismatch",
    ):
        service.record_action(
            user_id=1,
            proceeding_id=1,
            action_type="hearing",
            action_details="Details",
        )


def test_action_and_decision_audit_events(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    service.record_action(
        user_id=1,
        proceeding_id=1,
        action_type="hearing",
        action_details="Hearing conducted.",
    )
    service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Decision recorded.",
    )

    events = setup_j5d.execute(
        """
        SELECT event_type, actor_id, tenant_id, action
        FROM audit_events
        WHERE tenant_id = 'tenant-001'
        ORDER BY id
        """
    ).fetchall()

    event_types = [row["event_type"] for row in events]

    assert "judicial_action_recorded" in event_types
    assert "judicial_decision_recorded" in event_types

    matching = [
        row
        for row in events
        if row["event_type"] in {
            "judicial_action_recorded",
            "judicial_decision_recorded",
        }
    ]

    assert all(row["actor_id"] == 1 for row in matching)
    assert all(row["tenant_id"] == "tenant-001" for row in matching)


def test_multiple_decisions_are_allowed(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    first = service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="interim",
        decision_reason="First judicial decision.",
    )
    second = service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="final",
        decision_reason="Second judicial decision.",
    )

    assert first.id != second.id

    count = setup_j5d.execute(
        """
        SELECT COUNT(*)
        FROM judicial_decisions
        WHERE tenant_id = 'tenant-001'
          AND proceeding_id = 1
        """
    ).fetchone()[0]

    assert count == 2


def test_judicial_records_do_not_mutate_dispute_service_act_or_tp(
    setup_j5d,
):
    before_dispute = setup_j5d.execute(
        """
        SELECT status, resolution, resolution_reason, resolved_by_user_id
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    before_service_act = setup_j5d.execute(
        """
        SELECT status, cancellation_reason
        FROM service_acts
        WHERE id = 1
        """
    ).fetchone()

    before_tp = setup_j5d.execute(
        "SELECT id, tenant_id, user_id, service_act_id, amount, transaction_type, reference FROM talent_point_transactions ORDER BY id"
    ).fetchall()

    service = JudicialActionsDecisionsService(setup_j5d)

    service.record_action(
        user_id=1,
        proceeding_id=1,
        action_type="hearing",
        action_details="Hearing conducted.",
    )
    service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Decision recorded.",
    )

    after_dispute = setup_j5d.execute(
        """
        SELECT status, resolution, resolution_reason, resolved_by_user_id
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    after_service_act = setup_j5d.execute(
        """
        SELECT status, cancellation_reason
        FROM service_acts
        WHERE id = 1
        """
    ).fetchone()

    assert tuple(after_dispute) == tuple(before_dispute)
    assert tuple(after_service_act) == tuple(before_service_act)

    after_tp = setup_j5d.execute(
        """
        SELECT id, tenant_id, user_id, service_act_id, amount,
               transaction_type, reference
        FROM talent_point_transactions
        ORDER BY id
        """
    ).fetchall()

    assert [tuple(row) for row in after_tp] == [
        tuple(row) for row in before_tp
    ]


def test_tenant_isolation_for_proceeding(setup_j5d):
    setup_j5d.execute(
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
        (
            2,
            "tenant-002",
            3,
            4,
            "Other tenant service act",
            "Other tenant description",
            "created",
        ),
    )

    setup_j5d.execute(
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
        (
            2,
            "tenant-002",
            2,
            3,
            "provider",
            "Other tenant dispute",
            "open",
        ),
    )

    setup_j5d.execute(
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
        (
            2,
            "tenant-002",
            2,
            2,
            "service_dispute",
            "active",
            None,
        ),
    )
    setup_j5d.commit()

    service = JudicialActionsDecisionsService(setup_j5d)

    with pytest.raises(
        ValueError,
        match="judicial authority jurisdiction mismatch|tenant mismatch",
    ):
        service.record_action(
            user_id=1,
            proceeding_id=2,
            action_type="hearing",
            action_details="Cross-tenant attempt.",
        )

    assert (
        setup_j5d.execute(
            """
            SELECT COUNT(*)
            FROM judicial_actions
            WHERE tenant_id = 'tenant-002'
            """
        ).fetchone()[0]
        == 0
    )


def test_decision_does_not_close_proceeding(setup_j5d):
    service = JudicialActionsDecisionsService(setup_j5d)

    service.record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Decision recorded.",
    )

    status = setup_j5d.execute(
        """
        SELECT status
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()["status"]

    assert status == "active"
