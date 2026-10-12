"""Experimental DSL-to-boundary-preservation orchestration.

This module composes the typed semantic IR with the existing P4
boundary transformation/evaluation primitives. It adds no DSL syntax,
semantic inference, authorization, or governance behavior.
"""

from collections.abc import Iterable

from dsl_ir_v2 import CompiledPreservationIR
from p3_relation_algebra import Fact
from p4_boundary_transform import (
    Transformation,
    establish_correspondence,
    evaluate_correspondence,
    transform_facts,
)


def evaluate_compiled_transformation(
    compiled: CompiledPreservationIR,
    source_facts: Iterable[Fact],
    transformation: Transformation,
    *,
    scope: str,
) -> str:
    correspondence = establish_correspondence(
        compiled.boundary,
        transformation,
    )
    target_facts = transform_facts(source_facts, transformation)
    return evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope=scope,
    )


__all__ = [
    "evaluate_compiled_transformation",
]
