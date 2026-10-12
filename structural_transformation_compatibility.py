"""Experimental structural transformation compatibility predicate.

This prototype evaluates only whether a concrete protected boundary has a
structurally valid correspondence under an explicit transformation. It does
not infer general semantic compatibility, authorization, or governance.
"""

from boundary_correspondence_validation import validate_boundary_correspondence
from p4_boundary_transform import Boundary, Transformation, establish_correspondence


def structurally_compatible_boundary(
    boundary: Boundary,
    transformation: Transformation,
) -> bool:
    try:
        correspondence = establish_correspondence(boundary, transformation)
    except ValueError:
        return False

    return validate_boundary_correspondence(
        correspondence.source,
        correspondence.target,
        transformation,
    )


__all__ = ["structurally_compatible_boundary"]
