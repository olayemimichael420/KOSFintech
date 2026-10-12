"""Experimental protected-boundary DSL transformation pipeline v2.

Unlike pipeline v1, this module keeps the compiled boundary fixed while
transforming facts. It adds no DSL syntax, semantic inference, authorization,
or governance behavior.
"""

from collections.abc import Iterable

from dsl_ir_v2 import CompiledPreservationIR
from p3_relation_algebra import Conformance, Fact, contradiction_exists
from p4_boundary_transform import Transformation, transform_facts


def evaluate_protected_transformation(
    compiled: CompiledPreservationIR,
    source_facts: Iterable[Fact],
    transformation: Transformation,
    *,
    scope: str,
) -> str:
    source_facts = tuple(source_facts)
    target_facts = transform_facts(source_facts, transformation)

    before = (
        Conformance.CONFLICT
        if contradiction_exists(
            (compiled.boundary,),
            source_facts,
            scope=scope,
        )
        else Conformance.ALLOW
    )

    after = (
        Conformance.CONFLICT
        if contradiction_exists(
            (compiled.boundary,),
            target_facts,
            scope=scope,
        )
        else Conformance.ALLOW
    )

    return "PRESERVED" if before is after else "VIOLATED"


__all__ = [
    "evaluate_protected_transformation",
]
