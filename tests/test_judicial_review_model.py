from models.judicial_review import (
    JudicialReview,
    JudicialReviewStatus,
    JudicialReviewType,
)


def test_judicial_review_model_defaults_to_proposed():
    review = JudicialReview(
        id=None,
        tenant_id="tenant-001",
        proceeding_id=10,
        decision_id=20,
        originating_judicial_authority_id=30,
        jurisdiction_id=40,
        review_type=JudicialReviewType.REVIEW,
        initiated_by=50,
        grounds="procedural concern",
    )

    assert review.review_type == JudicialReviewType.REVIEW
    assert review.status == JudicialReviewStatus.PROPOSED
    assert review.proceeding_id == 10
    assert review.decision_id == 20
    assert review.originating_judicial_authority_id == 30
    assert review.jurisdiction_id == 40
    assert review.initiated_by == 50


def test_judicial_review_supports_appeal_as_a_descriptive_type():
    review = JudicialReview(
        id=None,
        tenant_id="tenant-001",
        proceeding_id=10,
        decision_id=20,
        originating_judicial_authority_id=30,
        jurisdiction_id=40,
        review_type=JudicialReviewType.APPEAL,
        initiated_by=50,
        grounds="appeal grounds",
    )

    assert review.review_type == JudicialReviewType.APPEAL
    assert review.status == JudicialReviewStatus.PROPOSED


def test_judicial_review_is_immutable():
    review = JudicialReview(
        id=None,
        tenant_id="tenant-001",
        proceeding_id=10,
        decision_id=20,
        originating_judicial_authority_id=30,
        jurisdiction_id=40,
        review_type=JudicialReviewType.REVIEW,
        initiated_by=50,
        grounds="procedural concern",
    )

    try:
        review.grounds = "changed"
        assert False, "JudicialReview should be immutable"
    except Exception as exc:
        assert exc.__class__.__name__ == "FrozenInstanceError"
