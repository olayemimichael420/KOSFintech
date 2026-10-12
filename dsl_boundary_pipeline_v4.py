"""Experimental correspondence-validated DSL transformation pipeline v4.

This prototype derives a candidate target boundary, validates its
correspondence against the protected source boundary, and only then
evaluates transformed facts. It adds no DSL syntax, semantic inference,
authorization, or governance behavior.
"""

from collections.abc import Iterable

from boundary_correspondence_validation import validate_boundary_correspondence
from transformation_compatibility import transformation_preserves_constraint
from dsl_ir_v2 import CompiledPreservationIR
from p3_relation_algebra import Fact
from p4_boundary_transform import (
    Transformation,
    establish_correspondence,
    evaluate_correspondence,
    transform_facts,
)


def evaluate_validated_transformation(
    compiled: CompiledPreservationIR,
    source_facts: Iterable[Fact],
    transformation: Transformation,
    *,
    scope: str,
) -> str:
    source_facts = tuple(source_facts)
    correspondence = establish_correspondence(
        compiled.boundary,
        transformation,
    )

    if not validate_boundary_correspondence(
        correspondence.source,
        correspondence.target,
        transformation,
    ):
        return "VIOLATED"

    compatibility = transformation_preserves_constraint(
        compiled.constraint,
        transformation,
    )
    if compatibility is not True:
        return "VIOLATED"

    target_facts = transform_facts(source_facts, transformation)

    return evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope=scope,
    )


__all__ = [
    "evaluate_validated_transformation",
]
