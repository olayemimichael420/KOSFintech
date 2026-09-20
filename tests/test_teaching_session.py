from models.teaching_session import TeachingSession


def test_teaching_session_constructs_with_required_fields():
    session = TeachingSession(
        id=None,
        tenant_id="tenant-1",
        name="2026 Teaching Session",
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    assert session.id is None
    assert session.tenant_id == "tenant-1"
    assert session.name == "2026 Teaching Session"
    assert session.start_date == "2026-01-01"
    assert session.end_date == "2026-12-31"
    assert session.status == "active"


def test_teaching_session_is_immutable():
    session = TeachingSession(
        id=None,
        tenant_id="tenant-1",
        name="2026 Teaching Session",
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    try:
        session.name = "Changed"
        assert False, "TeachingSession should be immutable"
    except AttributeError:
        pass
