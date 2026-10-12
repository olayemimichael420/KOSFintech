"""P10 isolated transformation of derived semantic candidates."""

from dataclasses import replace

from dsl_ir_v2 import PreservationConstraintIR
from p3_relation_algebra import Boundary, Fact, contradiction_exists
from p4_boundary_transform import Transformation, transform_boundaries, transform_facts
from p9_semantic_derivation import DerivedCandidate
from transformation_compatibility import transformation_preserves_constraint


def _has_conflicting_mapping(transformation: Transformation) -> bool:
    seen = {}
    for source, target in transformation.mapping:
        previous = seen.get(source)
        if previous is not None and previous != target:
            return True
        seen[source] = target
    return False


def _has_non_injective_mapping(transformation: Transformation) -> bool:
    seen_targets = set()
    for source, target in transformation.mapping:
        if target in seen_targets:
            return True
        seen_targets.add(target)
    return False


def validate_derived_candidate_correspondence(
    source_candidate: DerivedCandidate,
    target_candidate: DerivedCandidate,
    transformation: Transformation,
) -> bool:
    if _has_conflicting_mapping(transformation):
        return False
    if _has_non_injective_mapping(transformation):
        return False

    mapping = dict(transformation.mapping)
    endpoints = {source_candidate.source, source_candidate.target}
    endpoints.update(
        endpoint
        for fact in source_candidate.premises
        for endpoint in (fact.source, fact.target)
    )

    for endpoint in endpoints:
        if endpoint not in mapping:
            return False

    expected = {mapping[source_candidate.source], mapping[source_candidate.target]}
    actual = {target_candidate.source, target_candidate.target}

    if expected != actual or target_candidate.scope != source_candidate.scope:
        return False

    if target_candidate.relation != source_candidate.relation:
        return False

    expected_premises = transform_facts(
        source_candidate.premises,
        transformation,
    )
    return target_candidate.premises == expected_premises


def transform_derived_candidate(
    candidate: DerivedCandidate,
    transformation: Transformation,
) -> DerivedCandidate:
    candidate_fact = transform_facts(
        (Fact(candidate.source, candidate.relation, candidate.target, candidate.scope),),
        transformation,
    )[0]
    transformed_premises = transform_facts(candidate.premises, transformation)
    return replace(
        candidate,
        source=candidate_fact.source,
        relation=candidate_fact.relation,
        target=candidate_fact.target,
        premises=transformed_premises,
    )


def evaluate_transformed_derived_candidate(
    source_candidate: DerivedCandidate,
    transformed_candidate: DerivedCandidate,
    source_boundaries,
    transformation: Transformation,
    preservation_constraint: PreservationConstraintIR,
    *,
    scope: str,
) -> str:
    compatibility = transformation_preserves_constraint(
        preservation_constraint, transformation
    )
    if compatibility is not True:
        return "VIOLATED"

    if not validate_derived_candidate_correspondence(
        source_candidate, transformed_candidate, transformation
    ):
        return "VIOLATED"

    try:
        target_boundaries = transform_boundaries(source_boundaries, transformation)
    except ValueError:
        return "VIOLATED"

    derived_fact = Fact(
        transformed_candidate.source,
        transformed_candidate.relation,
        transformed_candidate.target,
        transformed_candidate.scope,
    )

    if contradiction_exists(target_boundaries, (derived_fact,), scope=scope):
        return "REJECTED"

    return "ACCEPTED"


__all__ = [
    "transform_derived_candidate",
    "validate_derived_candidate_correspondence",
    "evaluate_transformed_derived_candidate",
]
