from models.teaching_series import TeachingSeries


def test_teaching_series_defaults_to_active():
    series = TeachingSeries(
        id=None,
        tenant_id="tenant-cmos",
        teaching_session_id=1,
        name="Faith Series",
        start_date="2026-01-10",
        end_date="2026-02-10",
    )

    assert series.status == "active"


def test_teaching_series_preserves_core_fields():
    series = TeachingSeries(
        id=7,
        tenant_id="tenant-cmos",
        teaching_session_id=3,
        name="Kingdom Series",
        start_date="2026-03-01",
        end_date="2026-03-31",
        status="inactive",
    )

    assert series.id == 7
    assert series.tenant_id == "tenant-cmos"
    assert series.teaching_session_id == 3
    assert series.name == "Kingdom Series"
    assert series.start_date == "2026-03-01"
    assert series.end_date == "2026-03-31"
    assert series.status == "inactive"
