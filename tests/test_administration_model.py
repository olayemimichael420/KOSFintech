from models.administration import Administration


def test_administration_can_represent_a_school():
    administration = Administration(
        id=1,
        tenant_id="tenant-school-001",
        name="Example School",
        administration_type="school",
    )

    assert administration.tenant_id == "tenant-school-001"
    assert administration.name == "Example School"
    assert administration.administration_type == "school"
    assert administration.status == "active"


def test_administration_can_represent_other_domains():
    administration_types = (
        "community",
        "hospital",
        "hotel",
        "church",
    )

    for administration_type in administration_types:
        administration = Administration(
            id=None,
            tenant_id=f"tenant-{administration_type}",
            name=f"Example {administration_type}",
            administration_type=administration_type,
        )

        assert administration.administration_type == administration_type
        assert administration.status == "active"


def test_administration_is_immutable():
    administration = Administration(
        id=1,
        tenant_id="tenant-001",
        name="Example",
        administration_type="school",
    )

    try:
        administration.name = "Changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("Administration must be immutable")
