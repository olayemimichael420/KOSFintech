from models.grade import Grade


def test_grade_defaults():
    grade = Grade(
        id=None,
        tenant_id="tenant-a",
        name="A",
    )

    assert grade.id is None
    assert grade.tenant_id == "tenant-a"
    assert grade.name == "A"
    assert grade.description is None
    assert grade.minimum_score == 0
    assert grade.maximum_score == 0
    assert grade.status == "active"


def test_grade_accepts_score_range():
    grade = Grade(
        id=None,
        tenant_id="tenant-a",
        name="A",
        description="Excellent",
        minimum_score=80,
        maximum_score=100,
    )

    assert grade.minimum_score == 80
    assert grade.maximum_score == 100


def test_grade_is_frozen():
    grade = Grade(
        id=None,
        tenant_id="tenant-a",
        name="A",
        minimum_score=80,
        maximum_score=100,
    )

    try:
        grade.name = "B"
        assert False, "Grade should be immutable"
    except AttributeError:
        pass
