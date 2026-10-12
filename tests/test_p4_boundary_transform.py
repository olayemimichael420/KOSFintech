import pytest
"""P4 explicit transformation acceptance matrix."""

from p3_relation_algebra import Boundary, Conformance, Fact, Relation
from p4_boundary_transform import (
    BoundaryCorrespondence,
    transform_boundaries,
    transform_facts,
    Transformation,
    TransformationKind,
    verify_preservation,
)


def test_p4_canonicalization_preserves_boundary_semantics():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("B", Relation.SAME_AS, "A", scope="S")]
    result = verify_preservation(
        boundaries,
        facts,
        Transformation(TransformationKind.CANONICALIZE),
        scope="S",
    )
    assert result.before is Conformance.CONFLICT
    assert result.after is Conformance.CONFLICT
    assert result.preserved is True


def test_p4_rename_preserves_boundary_relationship():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]
    result = verify_preservation(
        boundaries,
        facts,
        Transformation(
            TransformationKind.RENAME,
            (("A", "X"), ("B", "Y")),
        ),
        scope="S",
    )
    assert result.before is Conformance.CONFLICT
    assert result.after is Conformance.CONFLICT
    assert result.preserved is True


def test_p4_rebind_that_changes_protected_relationship_is_detected():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]
    result = verify_preservation(
        boundaries,
        facts,
        Transformation(
            TransformationKind.REBIND,
            (("B", "C"),),
        ),
        scope="S",
    )
    assert result.before is Conformance.CONFLICT
    assert result.after is Conformance.ALLOW
    assert result.preserved is False



def test_p4_endpoint_collapse_is_not_boundary_preserving():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]

    with pytest.raises(ValueError, match="boundary endpoint collapse"):
        verify_preservation(
            boundaries,
            facts,
            Transformation(
                TransformationKind.RENAME,
                (("A", "X"), ("B", "X")),
            ),
            scope="S",
        )



def test_p4_transformed_boundary_preserves_endpoint_distinctness():
    boundaries = [Boundary("A", "B", scope="S")]
    transformed = transform_boundaries(
        boundaries,
        Transformation(
            TransformationKind.RENAME,
            (("A", "X"), ("B", "Y")),
        ),
    )
    assert transformed == frozenset({Boundary("X", "Y", scope="S")})


def test_p4_transformed_boundary_rejects_endpoint_collapse():
    boundaries = [Boundary("A", "B", scope="S")]

    with pytest.raises(ValueError, match="boundary endpoint collapse"):
        transform_boundaries(
            boundaries,
            Transformation(
                TransformationKind.RENAME,
                (("A", "X"), ("B", "X")),
            ),
        )


def test_p4_boundary_endpoint_mapping_must_be_injective():
    valid = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    collapse = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "X")),
    )

    assert len(dict(valid.mapping)) == len(set(dict(valid.mapping).values()))
    assert len(dict(collapse.mapping)) != len(set(dict(collapse.mapping).values()))


def test_p5_composed_renames_preserve_boundary_relationship():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]
    first = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    second = Transformation(
        TransformationKind.RENAME,
        (("X", "P"), ("Y", "Q")),
    )

    first_boundaries = transform_boundaries(boundaries, first)
    first_facts = transform_facts(facts, first)
    second_boundaries = transform_boundaries(first_boundaries, second)
    second_facts = transform_facts(first_facts, second)

    assert second_boundaries == frozenset({Boundary("P", "Q", scope="S")})
    assert second_facts == (Fact("P", Relation.SAME_AS, "Q", scope="S"),)


def test_p5_composed_rename_detects_second_step_endpoint_collapse():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]
    first = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    second = Transformation(
        TransformationKind.RENAME,
        (("X", "P"), ("Y", "P")),
    )

    first_boundaries = transform_boundaries(boundaries, first)
    first_facts = transform_facts(facts, first)

    with pytest.raises(ValueError, match="boundary endpoint collapse"):
        transform_boundaries(first_boundaries, second)


def test_p5_composed_mapping_matches_sequential_transformation():
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", Relation.SAME_AS, "B", scope="S")]
    first = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    second = Transformation(
        TransformationKind.RENAME,
        (("X", "P"), ("Y", "Q")),
    )
    composed = Transformation(
        TransformationKind.RENAME,
        (("A", "P"), ("B", "Q")),
    )

    sequential_boundaries = transform_boundaries(
        transform_boundaries(boundaries, first), second
    )
    sequential_facts = transform_facts(
        transform_facts(facts, first), second
    )
    composed_boundaries = transform_boundaries(boundaries, composed)
    composed_facts = transform_facts(facts, composed)

    assert sequential_boundaries == composed_boundaries
    assert sequential_facts == composed_facts


@pytest.mark.parametrize("relation", [Relation.SAME_AS, Relation.EQUIVALENT, Relation.IDENTITY])
def test_p5_rename_preserves_all_promotion_preserving_relations(relation):
    boundaries = [Boundary("A", "B", scope="S")]
    facts = [Fact("A", relation, "B", scope="S")]
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )

    transformed_boundaries = transform_boundaries(boundaries, transformation)
    transformed_facts = transform_facts(facts, transformation)

    assert transformed_boundaries == frozenset({Boundary("X", "Y", scope="S")})
    assert transformed_facts == (Fact("X", relation, "Y", scope="S"),)



def test_p6_boundary_correspondence_records_source_and_target():
    correspondence = BoundaryCorrespondence(
        source=Boundary("A", "B", scope="S"),
        target=Boundary("X", "Y", scope="S"),
    )

    assert correspondence.source == Boundary("A", "B", scope="S")
    assert correspondence.target == Boundary("X", "Y", scope="S")


def test_t1_dsl_derived_valid_transformation_is_preserved():
    from dsl_parser_v1 import parse_declaration
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import BoundaryCorrespondence, Transformation, TransformationKind, evaluate_correspondence, transform_boundaries, transform_facts
    d=parse_declaration(TEACHING_SUBJECT)
    assert "tenant boundary" in d.preserves
    source=Boundary("TenantA","TenantB",scope="tenant")
    facts=(Fact("TenantA",Relation.SAME_AS,"TenantB",scope="tenant"),)
    t=Transformation(TransformationKind.RENAME,(("TenantA","TenantX"),("TenantB","TenantY")))
    target=next(iter(transform_boundaries([source],t)))
    result=evaluate_correspondence(BoundaryCorrespondence(source,target),facts,transform_facts(facts,t),scope="tenant")
    assert result == "PRESERVED"


def test_t2_dsl_derived_adversarial_transformation_is_violated():
    from dsl_parser_v1 import parse_declaration
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import BoundaryCorrespondence, Transformation, TransformationKind, evaluate_correspondence, transform_facts
    d=parse_declaration(TEACHING_SUBJECT)
    assert "tenant boundary" in d.preserves
    source=Boundary("TenantA","TenantB",scope="tenant")
    facts=(Fact("TenantA",Relation.SAME_AS,"TenantB",scope="tenant"),)
    t=Transformation(TransformationKind.REBIND,(("TenantB","TenantC"),))
    result=evaluate_correspondence(BoundaryCorrespondence(source,source),facts,transform_facts(facts,t),scope="tenant")
    assert result == "VIOLATED"


def test_t3_unrelated_transformation_does_not_satisfy_protected_boundary():
    from dsl_parser_v1 import parse_declaration
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import BoundaryCorrespondence, Transformation, TransformationKind, evaluate_correspondence, transform_facts
    d=parse_declaration(TEACHING_SUBJECT)
    assert "tenant boundary" in d.preserves
    source=Boundary("TenantA","TenantB",scope="tenant")
    source_facts=(Fact("TenantA",Relation.SAME_AS,"TenantB",scope="tenant"),)
    unrelated=Transformation(TransformationKind.RENAME,(("OtherA","OtherX"),("OtherB","OtherY")))
    unrelated_facts=(Fact("OtherA",Relation.SAME_AS,"OtherB",scope="tenant"),)
    result=evaluate_correspondence(BoundaryCorrespondence(source,source),source_facts,transform_facts(unrelated_facts,unrelated),scope="tenant")
    assert result == "VIOLATED"


def test_m4_dsl_composed_valid_transformations_are_preserved():
    from dsl_parser_v1 import parse_declaration
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import BoundaryCorrespondence, Transformation, TransformationKind, evaluate_correspondence, transform_boundaries, transform_facts
    d=parse_declaration(TEACHING_SUBJECT)
    assert "tenant boundary" in d.preserves
    source=Boundary("TenantA","TenantB",scope="tenant")
    facts=(Fact("TenantA",Relation.SAME_AS,"TenantB",scope="tenant"),)
    t1=Transformation(TransformationKind.RENAME,(("TenantA","TenantX"),("TenantB","TenantY")))
    t2=Transformation(TransformationKind.RENAME,(("TenantX","TenantP"),("TenantY","TenantQ")))
    b1=next(iter(transform_boundaries([source],t1)))
    b2=next(iter(transform_boundaries([b1],t2)))
    f2=transform_facts(transform_facts(facts,t1),t2)
    result=evaluate_correspondence(BoundaryCorrespondence(source,b2),facts,f2,scope="tenant")
    assert result == "PRESERVED"


def test_m4_dsl_composed_adversarial_transformation_is_rejected():
    import pytest
    from dsl_parser_v1 import parse_declaration
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind, transform_boundaries
    d=parse_declaration(TEACHING_SUBJECT)
    assert "tenant boundary" in d.preserves
    source=Boundary("TenantA","TenantB",scope="tenant")
    t1=Transformation(TransformationKind.RENAME,(("TenantA","TenantX"),("TenantB","TenantY")))
    t2=Transformation(TransformationKind.RENAME,(("TenantX","TenantP"),("TenantY","TenantP")))
    b1=next(iter(transform_boundaries([source],t1)))
    with pytest.raises(ValueError, match="boundary endpoint collapse is not boundary-preserving"):
        transform_boundaries([b1],t2)
