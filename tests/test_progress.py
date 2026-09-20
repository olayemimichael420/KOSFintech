import pytest

from models.progress import Progress


def test_progress_constructs_with_expected_values():
    progress = Progress(
        id=1,
        tenant_id="tenant-cmos",
        membership_id=10,
        teaching_content_id=20,
        progress_date="2026-09-19",
        description="Demonstrated increased understanding of the teaching content",
        remark="Observed during follow-up activity",
        status="active",
    )

    assert progress.id == 1
    assert progress.tenant_id == "tenant-cmos"
    assert progress.membership_id == 10
    assert progress.teaching_content_id == 20
    assert progress.progress_date == "2026-09-19"
    assert progress.description == (
        "Demonstrated increased understanding of the teaching content"
    )
    assert progress.remark == "Observed during follow-up activity"
    assert progress.status == "active"


def test_progress_defaults_to_active():
    progress = Progress(
        id=None,
        tenant_id="tenant-cmos",
        membership_id=10,
        teaching_content_id=20,
        progress_date="2026-09-19",
        description="Recorded learning development",
    )

    assert progress.status == "active"
    assert progress.remark is None


def test_progress_is_frozen():
    progress = Progress(
        id=None,
        tenant_id="tenant-cmos",
        membership_id=10,
        teaching_content_id=20,
        progress_date="2026-09-19",
        description="Recorded learning development",
    )

    with pytest.raises((AttributeError, TypeError)):
        progress.description = "changed"
