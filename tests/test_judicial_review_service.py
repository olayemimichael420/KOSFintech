import pytest

from services.judicial_actions_decisions_service import (
    JudicialActionsDecisionsService,
)
from services.judicial_review_service import JudicialReviewService
from models.judicial_review import (
    JudicialReviewStatus,
    JudicialReviewType,
)


def _create_decision(connection):
    return JudicialActionsDecisionsService(connection).record_decision(
        user_id=1,
        proceeding_id=1,
        decision_type="determination",
        decision_reason="Evidence reviewed and determination recorded.",
    )


def test_record_review_success(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    review = service.record_review(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        review_type="review",
        grounds="The decision requires constitutional review.",
    )

    assert review.id is not None
    assert review.tenant_id == "tenant-001"
    assert review.proceeding_id == 1
    assert review.decision_id == decision.id
    assert review.originating_judicial_authority_id == 1
    assert review.jurisdiction_id == 1
    assert review.review_type == JudicialReviewType.REVIEW
    assert review.initiated_by == 1
    assert review.grounds == (
        "The decision requires constitutional review."
    )
    assert review.status == JudicialReviewStatus.PROPOSED
    assert review.recorded_at is not None


def test_record_appeal_is_descriptive_proposed_type(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    review = service.record_review(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        review_type="appeal",
        grounds="The decision is challenged on stated grounds.",
    )

    assert review.review_type == JudicialReviewType.APPEAL
    assert review.status == JudicialReviewStatus.PROPOSED


def test_requires_review_grounds(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    with pytest.raises(ValueError, match="review grounds is required"):
        service.record_review(
            user_id=1,
            proceeding_id=1,
            decision_id=decision.id,
            review_type="review",
            grounds=" ",
        )


def test_rejects_invalid_review_type(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    with pytest.raises(ValueError, match="invalid judicial review type"):
        service.record_review(
            user_id=1,
            proceeding_id=1,
            decision_id=decision.id,
            review_type="invalid",
            grounds="Grounds",
        )


def test_requires_existing_proceeding(setup_j5d):
    service = JudicialReviewService(setup_j5d)

    with pytest.raises(ValueError, match="judicial proceeding not found"):
        service.record_review(
            user_id=1,
            proceeding_id=999,
            decision_id=999,
            review_type="review",
            grounds="Grounds",
        )


def test_requires_existing_decision(setup_j5d):
    service = JudicialReviewService(setup_j5d)

    with pytest.raises(ValueError, match="judicial decision not found"):
        service.record_review(
            user_id=1,
            proceeding_id=1,
            decision_id=999,
            review_type="review",
            grounds="Grounds",
        )


def test_decision_must_belong_to_proceeding(setup_j5d):
    decision = _create_decision(setup_j5d)

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
            "tenant-001",
            1,
            1,
            "service_dispute",
            "active",
            1,
        ),
    )
    setup_j5d.commit()

    service = JudicialReviewService(setup_j5d)

    with pytest.raises(
        ValueError,
        match="judicial decision does not belong to proceeding",
    ):
        service.record_review(
            user_id=1,
            proceeding_id=2,
            decision_id=decision.id,
            review_type="review",
            grounds="Grounds",
        )


def test_rejects_decision_authority_jurisdiction_mismatch(setup_j5d):
    decision = _create_decision(setup_j5d)

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
        UPDATE judicial_decisions
        SET judicial_authority_id = 1
        WHERE id = ?
        """,
        (decision.id,),
    )
    setup_j5d.execute(
        """
        UPDATE judicial_proceedings
        SET jurisdiction_id = 3
        WHERE id = 1
        """,
    )
    setup_j5d.commit()

    service = JudicialReviewService(setup_j5d)

    with pytest.raises(
        ValueError,
        match="judicial decision authority jurisdiction mismatch",
    ):
        service.record_review(
            user_id=1,
            proceeding_id=1,
            decision_id=decision.id,
            review_type="review",
            grounds="Grounds",
        )


def test_requires_active_initiator_authority(setup_j5d):
    decision = _create_decision(setup_j5d)

    setup_j5d.execute(
        """
        UPDATE judicial_authorities
        SET status = 'suspended'
        WHERE id = 1
        """
    )
    setup_j5d.commit()

    service = JudicialReviewService(setup_j5d)

    with pytest.raises(ValueError, match="no active judicial authority"):
        service.record_review(
            user_id=1,
            proceeding_id=1,
            decision_id=decision.id,
            review_type="review",
            grounds="Grounds",
        )


def test_review_is_audit_record_only(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    before_proceeding = setup_j5d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    review = service.record_review(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        review_type="appeal",
        grounds="Grounds",
    )

    after_proceeding = setup_j5d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    assert review.status == JudicialReviewStatus.PROPOSED
    assert after_proceeding["status"] == before_proceeding["status"]
    assert after_proceeding["closed_at"] == before_proceeding["closed_at"]
    assert after_proceeding["closure_reason"] == before_proceeding["closure_reason"]


def test_review_audit_event(setup_j5d):
    decision = _create_decision(setup_j5d)
    service = JudicialReviewService(setup_j5d)

    review = service.record_review(
        user_id=1,
        proceeding_id=1,
        decision_id=decision.id,
        review_type="review",
        grounds="Grounds",
    )

    event = setup_j5d.execute(
        """
        SELECT event_type, actor_id, tenant_id, action
        FROM audit_events
        WHERE tenant_id = 'tenant-001'
          AND event_type = 'judicial_review_recorded'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    assert event is not None
    assert event["actor_id"] == 1
    assert event["tenant_id"] == "tenant-001"
    assert event["action"] == "record_judicial_review"
