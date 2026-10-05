"""Isolated P3 boundary-aware relation algebra prototype.

This experiment is intentionally independent of the v1 structural DSL parser.
It models only relation semantics, scoped boundaries, and promotion conformance.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Relation(str, Enum):
    EQUIVALENT = "EQUIVALENT"
    IDENTITY = "IDENTITY"
    SAME_AS = "SAME_AS"
    OWNS = "OWNS"
    MAY_GRANT = "may_grant"
    MAY_BE_USED_BY = "may_be_used_by"


PROMOTION_PRESERVING = frozenset({
    Relation.EQUIVALENT,
    Relation.IDENTITY,
    Relation.SAME_AS,
})

SYMMETRIC = PROMOTION_PRESERVING
TRANSITIVE_FOR_PROMOTION = PROMOTION_PRESERVING


@dataclass(frozen=True)
class Fact:
    source: str
    relation: Relation
    target: str
    scope: str = "default"


@dataclass(frozen=True)
class Boundary:
    left: str
    right: str
    scope: str = "default"

    def normalized(self) -> "Boundary":
        left, right = sorted((self.left, self.right))
        return Boundary(left, right, self.scope)


@dataclass(frozen=True)
class ScopeTransition:
    source_scope: str
    target_scope: str
    permitted: bool = False


class Conformance(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    CONFLICT = "CONFLICT"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    EVALUATE = "EVALUATE"


class BoundaryLedger:
    def __init__(self, boundaries: Iterable[Boundary] = ()) -> None:
        self._boundaries = {boundary.normalized() for boundary in boundaries}

    def add(self, boundary: Boundary) -> None:
        self._boundaries.add(boundary.normalized())

    def contains(self, left: str, right: str, scope: str) -> bool:
        return Boundary(left, right, scope).normalized() in self._boundaries

    def __len__(self) -> int:
        return len(self._boundaries)

    def as_frozenset(self) -> frozenset[Boundary]:
        return frozenset(self._boundaries)


def promotion_closure(
    facts: Iterable[Fact],
    *,
    scope: str,
) -> set[tuple[str, str]]:
    """Return ordered pairs connected only by promotion-preserving relations."""
    adjacency: dict[str, set[str]] = {}

    for fact in facts:
        if fact.scope != scope or fact.relation not in PROMOTION_PRESERVING:
            continue

        adjacency.setdefault(fact.source, set()).add(fact.target)
        if fact.relation in SYMMETRIC:
            adjacency.setdefault(fact.target, set()).add(fact.source)

    closure: set[tuple[str, str]] = set()
    for start in adjacency:
        stack = [start]
        seen = {start}
        while stack:
            current = stack.pop()
            if current != start:
                closure.add((start, current))
            for target in adjacency.get(current, ()):
                if target not in seen:
                    seen.add(target)
                    stack.append(target)
    return closure


def normalize_boundaries(boundaries: Iterable[Boundary]) -> frozenset[Boundary]:
    return frozenset(boundary.normalized() for boundary in boundaries)


def contradiction_exists(
    boundaries: Iterable[Boundary],
    facts: Iterable[Fact],
    *,
    scope: str,
) -> bool:
    ledger = normalize_boundaries(boundaries)
    closure = promotion_closure(facts, scope=scope)
    return any((boundary.left, boundary.right) in closure for boundary in ledger)


def evaluate(
    boundaries: Iterable[Boundary],
    facts: Iterable[Fact],
    *,
    source_scope: str,
    target_scope: str | None = None,
    transition: ScopeTransition | None = None,
) -> Conformance:
    """Evaluate a transformation without silently changing scope.

    Same-scope transformations are checked directly. A cross-scope import is
    blocked unless an explicit permitted transition is supplied; once supplied,
    the imported facts are evaluated in the target scope.
    """
    target_scope = target_scope or source_scope

    if target_scope != source_scope:
        if (
            transition is None
            or transition.source_scope != source_scope
            or transition.target_scope != target_scope
            or not transition.permitted
        ):
            return Conformance.SCOPE_VIOLATION
        return Conformance.EVALUATE if contradiction_exists(
            boundaries, facts, scope=target_scope
        ) else Conformance.ALLOW

    if contradiction_exists(boundaries, facts, scope=source_scope):
        return Conformance.CONFLICT
    return Conformance.ALLOW


def promotion_path_exists(facts: Iterable[Fact], source: str, target: str, *, scope: str) -> bool:
    return (source, target) in promotion_closure(facts, scope=scope)


__all__ = [
    "Boundary",
    "BoundaryLedger",
    "Conformance",
    "Fact",
    "Relation",
    "ScopeTransition",
    "contradiction_exists",
    "evaluate",
    "normalize_boundaries",
    "promotion_closure",
    "promotion_path_exists",
]
