from models.assessment import Assessment


def test_assessment_defaults():
    assessment = Assessment(
        id=None,
        tenant_id="tenant-cmos",
        teaching_content_id=17,
        name="Understanding Review",
        assessment_date="2026-09-19",
    )

    assert assessment.id is None
    assert assessment.tenant_id == "tenant-cmos"
    assert assessment.teaching_content_id == 17
    assert assessment.name == "Understanding Review"
    assert assessment.description is None
    assert assessment.assessment_date == "2026-09-19"
    assert assessment.status == "active"


def test_assessment_accepts_description_and_status():
    assessment = Assessment(
        id=1,
        tenant_id="tenant-cmos",
        teaching_content_id=17,
        name="Practical Demonstration",
        description="Observable demonstration of the taught material.",
        assessment_date="2026-09-19",
        status="inactive",
    )

    assert assessment.description == (
        "Observable demonstration of the taught material."
    )
    assert assessment.status == "inactive"


def test_assessment_is_immutable():
    assessment = Assessment(
        id=None,
        tenant_id="tenant-cmos",
        teaching_content_id=17,
        name="Understanding Review",
        assessment_date="2026-09-19",
    )

    try:
        assessment.name = "Changed"
        assert False, "Assessment should be immutable"
    except AttributeError:
        pass
