"""Experimental transformation-compatibility contract.

This prototype tests whether typed preservation constraints can be evaluated
against an explicit transformation compatibility contract. It does not
perform transformation, conformance evaluation, authorization, or governance.
"""

from dataclasses import dataclass

from dsl_ir_v2 import PreservationConstraintIR, PreservationKind
from p4_boundary_transform import Transformation, TransformationKind


@dataclass(frozen=True)
class TransformationCompatibilityContract:
    preservation_kind: PreservationKind
    preservation_value: str
    compatible_transformations: frozenset[TransformationKind] = frozenset()
    incompatible_transformations: frozenset[TransformationKind] = frozenset()

    def evaluate(
        self,
        constraint: PreservationConstraintIR,
        transformation: Transformation,
    ) -> bool | None:
        if (
            constraint.kind is not self.preservation_kind
            or constraint.value != self.preservation_value
        ):
            return None
        is_compatible = transformation.kind in self.compatible_transformations
        is_incompatible = transformation.kind in self.incompatible_transformations
        if is_compatible and is_incompatible:
            return None
        if is_compatible:
            return True
        if is_incompatible:
            return False
        return None


_TENANT_BOUNDARY_CONTRACT = TransformationCompatibilityContract(
    PreservationKind.BOUNDARY,
    "tenant boundary",
    compatible_transformations=frozenset({TransformationKind.RENAME}),
    incompatible_transformations=frozenset({TransformationKind.REBIND}),
)


def transformation_preserves_constraint(
    constraint: PreservationConstraintIR,
    transformation: Transformation,
) -> bool | None:
    return _TENANT_BOUNDARY_CONTRACT.evaluate(constraint, transformation)


__all__ = [
    "TransformationCompatibilityContract",
    "transformation_preserves_constraint",
]
