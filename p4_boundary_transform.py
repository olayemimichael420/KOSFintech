"""P4 explicit boundary-preserving transformation prototype."""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from p3_relation_algebra import (
    Boundary,
    Conformance,
    Fact,
    Relation,
    contradiction_exists,
    normalize_boundaries,
    normalize_facts,
)


class TransformationKind(str, Enum):
    CANONICALIZE = "CANONICALIZE"
    RENAME = "RENAME"
    REBIND = "REBIND"


@dataclass(frozen=True)
class Transformation:
    kind: TransformationKind
    mapping: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class BoundaryCorrespondence:
    source: Boundary
    target: Boundary


@dataclass(frozen=True)
class PreservationResult:
    before: Conformance
    after: Conformance
    preserved: bool


def _mapping_dict(transformation: Transformation) -> dict[str, str]:
    return dict(transformation.mapping)


def transform_facts(
    facts: Iterable[Fact],
    transformation: Transformation,
) -> tuple[Fact, ...]:
    facts = tuple(facts)

    if transformation.kind is TransformationKind.CANONICALIZE:
        return normalize_facts(facts)

    mapping = _mapping_dict(transformation)
    transformed = []
    for fact in facts:
        source = mapping.get(fact.source, fact.source)
        target = mapping.get(fact.target, fact.target)
        transformed.append(Fact(source, fact.relation, target, fact.scope))
    return normalize_facts(transformed)


def transform_boundaries(
    boundaries: Iterable[Boundary],
    transformation: Transformation,
) -> frozenset[Boundary]:
    boundaries = tuple(boundaries)

    if transformation.kind is TransformationKind.CANONICALIZE:
        return normalize_boundaries(boundaries)

    mapping = _mapping_dict(transformation)

    transformed = []
    for boundary in boundaries:
        left = mapping.get(boundary.left, boundary.left)
        right = mapping.get(boundary.right, boundary.right)
        if boundary.left != boundary.right and left == right:
            raise ValueError("boundary endpoint collapse is not boundary-preserving")
        transformed.append(Boundary(left, right, boundary.scope))

    return normalize_boundaries(transformed)


def establish_correspondence(
    source: Boundary,
    transformation: Transformation,
) -> BoundaryCorrespondence:
    target = next(iter(transform_boundaries((source,), transformation)))
    return BoundaryCorrespondence(source=source, target=target)


def verify_preservation(
    boundaries: Iterable[Boundary],
    source_facts: Iterable[Fact],
    transformation: Transformation,
    *,
    scope: str,
) -> PreservationResult:
    boundaries = tuple(boundaries)
    source_facts = tuple(source_facts)
    transformed_facts = transform_facts(source_facts, transformation)

    before = (
        Conformance.CONFLICT
        if contradiction_exists(boundaries, source_facts, scope=scope)
        else Conformance.ALLOW
    )

    protected_after_boundaries = (
        transform_boundaries(boundaries, transformation)
        if transformation.kind is TransformationKind.RENAME
        else boundaries
    )

    after = (
        Conformance.CONFLICT
        if contradiction_exists(
            protected_after_boundaries,
            transformed_facts,
            scope=scope,
        )
        else Conformance.ALLOW
    )

    return PreservationResult(
        before=before,
        after=after,
        preserved=before is after,
    )


def evaluate_correspondence(
    correspondence: BoundaryCorrespondence,
    source_facts: Iterable[Fact],
    target_facts: Iterable[Fact],
    *,
    scope: str,
) -> str:
    before = (
        Conformance.CONFLICT
        if contradiction_exists(
            [correspondence.source], source_facts, scope=scope
        )
        else Conformance.ALLOW
    )
    after = (
        Conformance.CONFLICT
        if contradiction_exists(
            [correspondence.target], target_facts, scope=scope
        )
        else Conformance.ALLOW
    )
    return 'PRESERVED' if before is after else 'VIOLATED'


__all__ = [
    "BoundaryCorrespondence",
    "PreservationResult",
    "Transformation",
    "TransformationKind",
    "transform_boundaries",
    "transform_facts",
    "verify_preservation",
    "evaluate_correspondence",
    "establish_correspondence",
]
