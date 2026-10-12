"""Experimental correspondence-gated DSL transformation pipeline v3.

This prototype separates candidate target-boundary derivation from
preservation evaluation. It adds no DSL syntax, semantic inference,
authorization, or governance behavior.
"""

from collections.abc import Iterable

from dsl_ir_v2 import CompiledPreservationIR
from p3_relation_algebra import Fact
from p4_boundary_transform import (
    BoundaryCorrespondence,
    Transformation,
    establish_correspondence,
    evaluate_correspondence,
    transform_facts,
)


def evaluate_correspondence_gated_transformation(
    compiled: CompiledPreservationIR,
    source_facts: Iterable[Fact],
    transformation: Transformation,
    *,
    scope: str,
) -> str:
    source_facts = tuple(source_facts)
    target_facts = transform_facts(source_facts, transformation)

    correspondence = establish_correspondence(
        compiled.boundary,
        transformation,
    )

    return evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope=scope,
    )


__all__ = [
    "evaluate_correspondence_gated_transformation",
]
