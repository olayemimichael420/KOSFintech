from models.result import Result


def test_result_defaults():
    result = Result(
        id=None,
        tenant_id="tenant-a",
        assessment_id=1,
        membership_id=2,
        grade_id=3,
        result="Completed the assessment requirements",
        result_date="2026-09-19",
    )

    assert result.id is None
    assert result.tenant_id == "tenant-a"
    assert result.assessment_id == 1
    assert result.membership_id == 2
    assert result.grade_id == 3
    assert result.result == "Completed the assessment requirements"
    assert result.result_date == "2026-09-19"
    assert result.remark is None
    assert result.status == "active"


def test_result_accepts_remark_and_status():
    result = Result(
        id=None,
        tenant_id="tenant-a",
        assessment_id=1,
        membership_id=2,
        grade_id=3,
        result="Requires further learning activity",
        result_date="2026-09-19",
        remark="Follow-up teaching recommended",
        status="inactive",
    )

    assert result.remark == "Follow-up teaching recommended"
    assert result.status == "inactive"


def test_result_is_frozen():
    result = Result(
        id=None,
        tenant_id="tenant-a",
        assessment_id=1,
        membership_id=2,
        grade_id=3,
        result="Demonstrated understanding",
        result_date="2026-09-19",
    )

    try:
        result.result = "Changed"
        assert False, "Result should be immutable"
    except AttributeError:
        pass
