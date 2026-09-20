from models.teaching_content import TeachingContent


def test_teaching_content_defaults():
    content = TeachingContent(
        id=None,
        tenant_id="tenant-cmos",
        teaching_focus_id=1,
        name="Introduction",
    )

    assert content.id is None
    assert content.tenant_id == "tenant-cmos"
    assert content.teaching_focus_id == 1
    assert content.name == "Introduction"
    assert content.description is None
    assert content.sequence is None
    assert content.status == "active"


def test_teaching_content_supports_ordered_content():
    content = TeachingContent(
        id=None,
        tenant_id="tenant-cmos",
        teaching_focus_id=7,
        name="Lesson Two",
        description="Second teaching content item.",
        sequence=2,
    )

    assert content.sequence == 2
    assert content.description == "Second teaching content item."
