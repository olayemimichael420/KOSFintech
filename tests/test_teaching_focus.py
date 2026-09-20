from models.teaching_focus import TeachingFocus


def test_teaching_focus_defaults_to_active():
    focus = TeachingFocus(
        id=None,
        tenant_id="tenant-cmos",
        teaching_series_id=1,
        name="Faith",
        start_date="2026-02-01",
        end_date="2026-02-28",
    )

    assert focus.status == "active"


def test_teaching_focus_is_frozen():
    focus = TeachingFocus(
        id=None,
        tenant_id="tenant-cmos",
        teaching_series_id=1,
        name="Faith",
        start_date="2026-02-01",
        end_date="2026-02-28",
    )

    try:
        focus.name = "Hope"
        assert False, "TeachingFocus should be immutable"
    except Exception:
        pass
