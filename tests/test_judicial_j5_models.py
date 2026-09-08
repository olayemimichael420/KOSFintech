from models.judicial_action import JudicialAction
from models.judicial_decision import JudicialDecision
from models.judicial_proceeding import (
    JudicialProceeding,
    JudicialProceedingStatus,
)


def test_judicial_proceeding_defaults_to_proposed():
    proceeding = JudicialProceeding(
        id=None,
        tenant_id="tenant-001",
        dispute_id=10,
        jurisdiction_id=20,
        proceeding_type="dispute_adjudication",
    )

    assert proceeding.status == JudicialProceedingStatus.PROPOSED
    assert proceeding.opened_by_authority_id is None
    assert proceeding.opened_at is None
    assert proceeding.closed_at is None
    assert proceeding.closure_reason is None


def test_judicial_proceeding_preserves_authority_opening_provenance():
    proceeding = JudicialProceeding(
        id=1,
        tenant_id="tenant-001",
        dispute_id=10,
        jurisdiction_id=20,
        proceeding_type="dispute_adjudication",
        status=JudicialProceedingStatus.OPEN,
        opened_by_authority_id=30,
        opened_at="2026-09-08T00:00:00+00:00",
    )

    assert proceeding.opened_by_authority_id == 30
    assert proceeding.status == JudicialProceedingStatus.OPEN


def test_judicial_action_records_authority_and_proceeding():
    action = JudicialAction(
        id=1,
        tenant_id="tenant-001",
        proceeding_id=40,
        judicial_authority_id=30,
        action_type="review_evidence",
        action_details="Evidence reviewed.",
        acted_at="2026-09-08T00:00:00+00:00",
    )

    assert action.proceeding_id == 40
    assert action.judicial_authority_id == 30
    assert action.action_type == "review_evidence"


def test_judicial_decision_records_authority_and_proceeding():
    decision = JudicialDecision(
        id=1,
        tenant_id="tenant-001",
        proceeding_id=40,
        judicial_authority_id=30,
        decision_type="recipient_favored",
        decision_reason="The evidence supports the recipient.",
        decided_at="2026-09-08T00:00:00+00:00",
    )

    assert decision.proceeding_id == 40
    assert decision.judicial_authority_id == 30
    assert decision.decision_type == "recipient_favored"
    assert decision.decision_reason == "The evidence supports the recipient."


def test_judicial_models_are_immutable():
    proceeding = JudicialProceeding(
        id=None,
        tenant_id="tenant-001",
        dispute_id=10,
        jurisdiction_id=20,
        proceeding_type="dispute_adjudication",
    )

    try:
        proceeding.status = JudicialProceedingStatus.OPEN
    except AttributeError:
        pass
    else:
        raise AssertionError("JudicialProceeding must be immutable")
