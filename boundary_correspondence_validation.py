"""Experimental protected-boundary correspondence validation.

This module validates whether a candidate target boundary is fully derived
from the protected source boundary by an explicit endpoint transformation.
It does not evaluate facts, infer semantics, authorize actions, or grant
governance authority.
"""

from p4_boundary_transform import Boundary, Transformation


def validate_boundary_correspondence(
    source: Boundary,
    target: Boundary,
    transformation: Transformation,
) -> bool:
    mapping = dict(transformation.mapping)

    if source.left not in mapping or source.right not in mapping:
        return False

    expected_left = mapping[source.left]
    expected_right = mapping[source.right]

    return (
        target.scope == source.scope
        and {
            target.left,
            target.right,
        }
        == {
            expected_left,
            expected_right,
        }
    )


__all__ = [
    "validate_boundary_correspondence",
]
