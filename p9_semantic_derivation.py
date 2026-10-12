"""P9 isolated semantic-derivation experiment.

This prototype wraps the existing P3 promotion closure without modifying
its relation algebra. It models a derived relation as a candidate that
must still pass protected-boundary evaluation.
"""

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from p3_relation_algebra import Boundary, Fact, Relation, contradiction_exists, promotion_closure


@dataclass(frozen=True)
class DerivationRule:
    premise_relation: Relation
    conclusion_relation: Relation


SAME_AS_TRANSITIVE_RULE = DerivationRule(
    Relation.SAME_AS,
    Relation.SAME_AS,
)


@dataclass(frozen=True)
class DerivedCandidate:
    source: str
    relation: Relation
    target: str
    scope: str
    premises: tuple[Fact, ...]


def _causal_path(facts, source, target, *, scope):
    scoped = tuple(f for f in facts if f.scope == scope and f.relation in {Relation.EQUIVALENT, Relation.IDENTITY, Relation.SAME_AS})
    adjacency = {}
    for fact in scoped:
        adjacency.setdefault(fact.source, []).append((fact.target, fact))
        adjacency.setdefault(fact.target, []).append((fact.source, fact))
    queue = deque([source])
    previous = {source: None}
    while queue:
        current = queue.popleft()
        if current == target:
            break
        for neighbor, fact in adjacency.get(current, []):
            if neighbor not in previous:
                previous[neighbor] = (current, fact)
                queue.append(neighbor)
    if target not in previous:
        return ()
    path = []
    current = target
    while current != source:
        prior, fact = previous[current]
        path.append(fact)
        current = prior
    path.reverse()
    return tuple(path)


def derive_same_as_candidates(
    facts: Iterable[Fact],
    *,
    scope: str,
    rule: DerivationRule = SAME_AS_TRANSITIVE_RULE,
) -> tuple[DerivedCandidate, ...]:
    facts = tuple(facts)
    if rule is not SAME_AS_TRANSITIVE_RULE:
        raise ValueError("unsupported derivation rule")

    scoped = tuple(
        fact
        for fact in facts
        if fact.scope == scope and fact.relation is rule.premise_relation
    )

    adjacency = {}
    for fact in scoped:
        adjacency.setdefault(fact.source, []).append((fact.target, fact))
        adjacency.setdefault(fact.target, []).append((fact.source, fact))

    candidates = []
    existing = {(fact.source, fact.target) for fact in scoped}

    for source in sorted(adjacency):
        queue = deque([source])
        previous = {source: None}
        while queue:
            current = queue.popleft()
            for neighbor, fact in adjacency.get(current, []):
                if neighbor not in previous:
                    previous[neighbor] = (current, fact)
                    queue.append(neighbor)

        for target in sorted(previous):
            if target == source or (source, target) in existing:
                continue
            premises = []
            current = target
            while current != source:
                prior, fact = previous[current]
                premises.append(fact)
                current = prior
            premises.reverse()
            candidates.append(
                DerivedCandidate(
                    source,
                    rule.conclusion_relation,
                    target,
                    scope,
                    tuple(premises),
                )
            )

    return tuple(candidates)


def evaluate_derived_candidate(
    candidate: DerivedCandidate,
    boundaries: Iterable[Boundary],
    *,
    scope: str,
) -> str:
    derived_fact = Fact(candidate.source, candidate.relation, candidate.target, candidate.scope)
    if contradiction_exists(boundaries, (derived_fact,), scope=scope):
        return "REJECTED"
    return "ACCEPTED"


__all__ = [
    "DerivationRule",
    "SAME_AS_TRANSITIVE_RULE",
    "DerivedCandidate",
    "derive_same_as_candidates",
    "evaluate_derived_candidate",
]
