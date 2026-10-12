from dataclasses import replace
from dsl_ir_v2 import PreservationConstraintIR, PreservationKind
from transformation_compatibility import TransformationCompatibilityContract
"""P10.1 transformation of derived semantic candidates."""

from p3_relation_algebra import Boundary, Fact, Relation
from p4_boundary_transform import Transformation, TransformationKind
from p9_semantic_derivation import DerivedCandidate, derive_same_as_candidates
from p10_transformed_derivation import (
    transform_derived_candidate,
    validate_derived_candidate_correspondence,
    evaluate_transformed_derived_candidate,
)


def test_p10_transforms_derived_candidate_and_provenance():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )

    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert (transformed.source, transformed.relation, transformed.target) == (
        "X", Relation.SAME_AS, "Z"
    )
    assert transformed.premises == (
        Fact("X", Relation.SAME_AS, "Y", scope="test"),
        Fact("Y", Relation.SAME_AS, "Z", scope="test"),
    )


def test_p10_partial_rename_does_not_silently_preserve_derivation():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )

    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert {transformed.source, transformed.target} == {"X", "C"}
    assert {
        frozenset((fact.source, fact.target))
        for fact in transformed.premises
    } == {
        frozenset(("X", "Y")),
        frozenset(("Y", "C")),
    }
    assert {transformed.source, transformed.target} != {"X", "Z"}


def test_p10_complete_mapping_validates_derived_candidate_correspondence():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert validate_derived_candidate_correspondence(
        candidate, transformed, transformation
    ) is True


def test_p10_partial_mapping_invalidates_derived_candidate_correspondence():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert validate_derived_candidate_correspondence(
        candidate, transformed, transformation
    ) is False


def test_p10_transformed_derived_candidate_is_rejected_by_target_boundary():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "C", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "REJECTED"


def test_p10_transformed_derived_candidate_is_accepted_without_target_conflict():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "ACCEPTED"



def test_p10_partial_mapping_of_derived_candidate_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "C", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"



def test_p10_endpoint_collapse_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "X")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "C", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"



def test_p10_scope_mutation_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    transformed = replace(transformed, scope="other")

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"



def test_p10_contradictory_compatibility_contract_does_not_accept():
    contract = TransformationCompatibilityContract(
        PreservationKind.BOUNDARY,
        "tenant boundary",
        compatible_transformations=frozenset({TransformationKind.RENAME}),
        incompatible_transformations=frozenset({TransformationKind.RENAME}),
    )
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    transformation = Transformation(TransformationKind.RENAME)

    result = contract.evaluate(constraint, transformation)

    assert result is not True


def test_p10_unsupported_canonicalize_is_violated():
    candidate = DerivedCandidate(
        source="A",
        relation=Relation.SAME_AS,
        target="C",
        scope="test",
        premises=(
            Fact("A", Relation.SAME_AS, "B", scope="test"),
            Fact("B", Relation.SAME_AS, "C", scope="test"),
        ),
    )
    transformation = Transformation(TransformationKind.CANONICALIZE)
    transformed = transform_derived_candidate(candidate, transformation)
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)

    result = evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("M", "N", scope="test"),),
        transformation,
        constraint,
        scope="test",
    )

    assert result == "VIOLATED"


def test_p10_semantically_incompatible_rebind_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.REBIND,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"


def test_p10_tampered_transformed_provenance_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    transformed = replace(
        transformed,
        premises=(
            Fact("X", Relation.SAME_AS, "Z", scope="test"),
        ),
    )

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"


def test_p10_substituted_transformed_provenance_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    transformed = replace(
        transformed,
        premises=(
            Fact("X", Relation.SAME_AS, "Z", scope="test"),
            Fact("Z", Relation.SAME_AS, "Y", scope="test"),
        ),
    )

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"


def test_p10_mutated_transformed_relation_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    transformed = replace(
        transformed,
        relation=Relation.OWNS,
    )

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"


def test_p10_mutated_transformed_premise_relation_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    transformed = replace(
        transformed,
        premises=(
            Fact("X", Relation.OWNS, "Y", scope="test"),
            Fact("Y", Relation.SAME_AS, "Z", scope="test"),
        ),
    )

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"


def test_p10_many_to_one_correspondence_is_violated_without_boundary_conflict():
    candidate = DerivedCandidate(
        source="A",
        relation=Relation.SAME_AS,
        target="C",
        scope="test",
        premises=(
            Fact("A", Relation.SAME_AS, "B", scope="test"),
            Fact("B", Relation.SAME_AS, "C", scope="test"),
        ),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        mapping=(("A", "X"), ("B", "Y"), ("C", "X")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)

    result = evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("M", "N", scope="test"),),
        transformation,
        constraint,
        scope="test",
    )

    assert result == "VIOLATED"


def test_p10_many_to_one_transformation_mapping_is_violated():
    candidate = DerivedCandidate(
        source="A",
        relation=Relation.SAME_AS,
        target="C",
        scope="test",
        premises=(
            Fact("A", Relation.SAME_AS, "B", scope="test"),
            Fact("B", Relation.SAME_AS, "C", scope="test"),
        ),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        mapping=(("A", "X"), ("B", "Y"), ("C", "X")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)

    result = evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        constraint,
        scope="test",
    )

    assert result == "VIOLATED"


def test_p10_conflicting_transformation_mapping_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("A", "Q"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)

    assert evaluate_transformed_derived_candidate(
        candidate,
        transformed,
        (Boundary("A", "D", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"



def test_p10_cross_layer_valid_structure_with_corrupted_provenance_is_violated():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("A", "X"), ("B", "Y"), ("C", "Z")),
    )
    transformed = transform_derived_candidate(candidate, transformation)
    corrupted = replace(
        transformed,
        premises=(
            Fact("X", Relation.SAME_AS, "Z", scope="test"),
        ),
    )

    assert evaluate_transformed_derived_candidate(
        candidate,
        corrupted,
        (Boundary("X", "Q", scope="test"),),
        transformation,
        PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY),
        scope="test",
    ) == "VIOLATED"
