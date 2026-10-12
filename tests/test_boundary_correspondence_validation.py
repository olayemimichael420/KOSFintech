from boundary_correspondence_validation import validate_boundary_correspondence
from p3_relation_algebra import Boundary
from p4_boundary_transform import Transformation, TransformationKind


def test_complete_endpoint_mapping_same_scope_is_valid():
    source = Boundary("TenantA", "TenantB", scope="tenant")
    target = Boundary("TenantX", "TenantY", scope="tenant")
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert validate_boundary_correspondence(
        source,
        target,
        transformation,
    ) is True


def test_partial_endpoint_mapping_is_invalid():
    source = Boundary("TenantA", "TenantB", scope="tenant")
    target = Boundary("TenantA", "TenantC", scope="tenant")
    transformation = Transformation(
        TransformationKind.REBIND,
        (("TenantB", "TenantC"),),
    )

    assert validate_boundary_correspondence(
        source,
        target,
        transformation,
    ) is False


def test_scope_change_is_invalid():
    source = Boundary("TenantA", "TenantB", scope="tenant")
    target = Boundary("TenantX", "TenantY", scope="global")
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert validate_boundary_correspondence(
        source,
        target,
        transformation,
    ) is False
