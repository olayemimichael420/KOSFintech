"""Experimental ordered transformation composition.

This module represents a transformation chain without assigning semantic
compatibility or authorization. It only preserves explicit stage order.
"""

from dataclasses import dataclass

from p3_relation_algebra import Fact
from p4_boundary_transform import Transformation, transform_facts
from dsl_ir_v2 import CompiledPreservationIR, PreservationConstraintIR
from transformation_compatibility import transformation_preserves_constraint
from boundary_correspondence_validation import validate_boundary_correspondence
from p4_boundary_transform import BoundaryCorrespondence, establish_correspondence, evaluate_correspondence, transform_boundaries


@dataclass(frozen=True)
class TransformationChain:
    stages: tuple[Transformation, ...] = ()

    def apply(self, facts: tuple[Fact, ...]) -> tuple[Fact, ...]:
        result = tuple(facts)
        for transformation in self.stages:
            result = transform_facts(result, transformation)
        return result


def compose_transformations(*transformations: Transformation) -> TransformationChain:
    return TransformationChain(tuple(transformations))


def chain_preserves_constraint(
    constraint: PreservationConstraintIR,
    chain: TransformationChain,
) -> bool:
    for transformation in chain.stages:
        if transformation_preserves_constraint(constraint, transformation) is not True:
            return False
    return True


def evaluate_chain_preservation(
    compiled: CompiledPreservationIR,
    source_facts: tuple[Fact, ...],
    chain: TransformationChain,
    *,
    scope: str,
) -> str:
    current_boundary = compiled.boundary
    current_facts = tuple(source_facts)

    for transformation in chain.stages:
        if transformation_preserves_constraint(
            compiled.constraint, transformation
        ) is not True:
            return "VIOLATED"

        try:
            correspondence = establish_correspondence(
                current_boundary, transformation
            )
        except ValueError:
            return "VIOLATED"

        if not validate_boundary_correspondence(
            correspondence.source,
            correspondence.target,
            transformation,
        ):
            return "VIOLATED"

        current_boundary = correspondence.target
        current_facts = transform_facts(current_facts, transformation)

    return evaluate_correspondence(
        BoundaryCorrespondence(compiled.boundary, current_boundary),
        tuple(source_facts),
        current_facts,
        scope=scope,
    )


__all__ = [
    "TransformationChain",
    "compose_transformations",
    "chain_preserves_constraint",
    "evaluate_chain_preservation",
]
