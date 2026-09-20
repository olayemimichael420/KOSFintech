from models.teaching_subject import TeachingSubject


def test_teaching_subject_defaults_to_active():
    subject = TeachingSubject(
        id=None,
        tenant_id="tenant-cmos",
        name="Faith",
    )

    assert subject.id is None
    assert subject.tenant_id == "tenant-cmos"
    assert subject.name == "Faith"
    assert subject.status == "active"


def test_teaching_subject_is_frozen():
    subject = TeachingSubject(
        id=None,
        tenant_id="tenant-cmos",
        name="Faith",
    )

    try:
        subject.name = "Hope"
        assert False, "TeachingSubject should be immutable"
    except AttributeError:
        pass
