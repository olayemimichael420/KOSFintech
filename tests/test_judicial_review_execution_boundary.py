import pytest

from models.judicial_review import JudicialReviewType
from services.judicial_review_service import JudicialReviewService


def _create_review(connection, review_type):
    decision = connection.execute(
        """
        SELECT id
        FROM judicial_decisions
        WHERE tenant_id = 'tenant-001'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if decision is None:
        from services.judicial_actions_decisions_service import (
            JudicialActionsDecisionsService,
        )

        decision = JudicialActionsDecisionsService(
            connection
        ).record_decision(
            user_id=1,
            proceeding_id=1,
            decision_type="determination",
            decision_reason="Decision for J7D boundary test.",
        )

    return JudicialReviewService(connection).record_review(
        user_id=1,
        proceeding_id=1,
        decision_id=decision["id"]
        if isinstance(decision, dict)
        else decision.id,
        review_type=review_type,
        grounds="Boundary test grounds.",
    )


def test_review_execution_must_fail_closed(setup_j5d):
    review = _create_review(setup_j5d, JudicialReviewType.REVIEW)

    from services.judicial_review_execution_boundary import (
        JudicialReviewExecutionBoundary,
    )

    decision = JudicialReviewExecutionBoundary(
        setup_j5d
    ).authorize_execution(
        review_id=review.id,
    )

    assert decision.allowed is False
    assert decision.reason == (
        "judicial review/appeal execution authority is not established"
    )


def test_appeal_execution_must_fail_closed(setup_j5d):
    review = _create_review(setup_j5d, JudicialReviewType.APPEAL)

    from services.judicial_review_execution_boundary import (
        JudicialReviewExecutionBoundary,
    )

    decision = JudicialReviewExecutionBoundary(
        setup_j5d
    ).authorize_execution(
        review_id=review.id,
    )

    assert decision.allowed is False
    assert decision.reason == (
        "judicial review/appeal execution authority is not established"
    )


def test_active_judicial_authority_does_not_grant_review_execution(
    setup_j5d,
):
    review = _create_review(setup_j5d, JudicialReviewType.APPEAL)

    from services.judicial_review_execution_boundary import (
        JudicialReviewExecutionBoundary,
    )

    authority = setup_j5d.execute(
        """
        SELECT status
        FROM judicial_authorities
        WHERE id = 1
        """
    ).fetchone()

    assert authority["status"] == "active"

    decision = JudicialReviewExecutionBoundary(
        setup_j5d
    ).authorize_execution(
        review_id=review.id,
    )

    assert decision.allowed is False


def test_fail_closed_boundary_does_not_mutate_review_or_proceeding(
    setup_j5d,
):
    review = _create_review(setup_j5d, JudicialReviewType.APPEAL)

    before_review = setup_j5d.execute(
        """
        SELECT status, grounds
        FROM judicial_reviews
        WHERE id = ?
        """,
        (review.id,),
    ).fetchone()

    before_proceeding = setup_j5d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    from services.judicial_review_execution_boundary import (
        JudicialReviewExecutionBoundary,
    )

    decision = JudicialReviewExecutionBoundary(
        setup_j5d
    ).authorize_execution(
        review_id=review.id,
    )

    after_review = setup_j5d.execute(
        """
        SELECT status, grounds
        FROM judicial_reviews
        WHERE id = ?
        """,
        (review.id,),
    ).fetchone()

    after_proceeding = setup_j5d.execute(
        """
        SELECT status, closed_at, closure_reason
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    assert decision.allowed is False
    assert after_review["status"] == before_review["status"]
    assert after_review["grounds"] == before_review["grounds"]
    assert after_proceeding["status"] == before_proceeding["status"]
    assert after_proceeding["closed_at"] == before_proceeding["closed_at"]
    assert (
        after_proceeding["closure_reason"]
        == before_proceeding["closure_reason"]
    )
