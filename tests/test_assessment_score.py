from models.assessment_score import AssessmentScore


def test_assessment_score_defaults():
    score = AssessmentScore(
        id=None,
        tenant_id="tenant-cmos",
        assessment_id=17,
        membership_id=23,
        score=82,
        scored_date="2026-09-19",
    )

    assert score.id is None
    assert score.tenant_id == "tenant-cmos"
    assert score.assessment_id == 17
    assert score.membership_id == 23
    assert score.score == 82
    assert score.scored_date == "2026-09-19"
    assert score.remark is None


def test_assessment_score_accepts_remark():
    score = AssessmentScore(
        id=1,
        tenant_id="tenant-cmos",
        assessment_id=17,
        membership_id=23,
        score=91,
        scored_date="2026-09-19",
        remark="Observable response recorded.",
    )

    assert score.remark == "Observable response recorded."


def test_assessment_score_is_immutable():
    score = AssessmentScore(
        id=None,
        tenant_id="tenant-cmos",
        assessment_id=17,
        membership_id=23,
        score=82,
        scored_date="2026-09-19",
    )

    try:
        score.score = 100
        assert False, "AssessmentScore should be immutable"
    except AttributeError:
        pass
