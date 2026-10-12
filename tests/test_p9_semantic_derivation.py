"""P9 isolated semantic-derivation acceptance tests."""

from p3_relation_algebra import Boundary, Fact, Relation
from p9_semantic_derivation import derive_same_as_candidates, evaluate_derived_candidate


def test_p9_derives_transitive_same_as_candidate():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )

    candidates = derive_same_as_candidates(facts, scope="test")

    assert any(
        candidate.source == "A" and candidate.target == "C"
        for candidate in candidates
    )


def test_p9_provenance_contains_only_causal_premises():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
        Fact("X", Relation.SAME_AS, "Y", scope="test"),
    )
    candidate = next(c for c in derive_same_as_candidates(facts, scope="test") if c.source == "A" and c.target == "C")
    assert candidate.premises == (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )


def test_p9_provenance_preserves_boundary_rejection():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    candidate = next(c for c in derive_same_as_candidates(facts, scope="test") if c.source == "A" and c.target == "C")
    assert evaluate_derived_candidate(candidate, (Boundary("A", "C", scope="test"),), scope="test") == "REJECTED"


def test_p9_derived_candidate_is_rejected_by_protected_boundary():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    boundaries = (Boundary("A", "C", scope="test"),)

    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )

    assert evaluate_derived_candidate(candidate, boundaries, scope="test") == "REJECTED"


def test_p9_derived_candidate_is_accepted_without_boundary_conflict():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
    )
    boundaries = (Boundary("A", "D", scope="test"),)

    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "C"
    )

    assert evaluate_derived_candidate(candidate, boundaries, scope="test") == "ACCEPTED"


def test_p9_derivation_does_not_cross_scope():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="other"),
    )

    candidates = derive_same_as_candidates(facts, scope="test")

    assert not any(
        candidate.source == "A" and candidate.target == "C"
        for candidate in candidates
    )


def test_p9_equivalent_does_not_infer_same_as():
    facts = (
        Fact("A", Relation.EQUIVALENT, "B", scope="test"),
        Fact("B", Relation.EQUIVALENT, "C", scope="test"),
    )

    candidates = derive_same_as_candidates(facts, scope="test")

    assert candidates == ()


def test_p9_identity_does_not_infer_same_as():
    facts = (
        Fact("A", Relation.IDENTITY, "B", scope="test"),
        Fact("B", Relation.IDENTITY, "C", scope="test"),
    )

    candidates = derive_same_as_candidates(facts, scope="test")

    assert candidates == ()


def test_p9_multistep_derivation_preserves_exact_causal_chain():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
        Fact("C", Relation.SAME_AS, "D", scope="test"),
        Fact("X", Relation.SAME_AS, "Y", scope="test"),
    )

    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "D"
    )

    assert candidate.premises == (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
        Fact("C", Relation.SAME_AS, "D", scope="test"),
    )


def test_p9_multistep_derivation_remains_boundary_rejected():
    facts = (
        Fact("A", Relation.SAME_AS, "B", scope="test"),
        Fact("B", Relation.SAME_AS, "C", scope="test"),
        Fact("C", Relation.SAME_AS, "D", scope="test"),
    )

    candidate = next(
        candidate
        for candidate in derive_same_as_candidates(facts, scope="test")
        if candidate.source == "A" and candidate.target == "D"
    )

    assert evaluate_derived_candidate(
        candidate,
        (Boundary("A", "D", scope="test"),),
        scope="test",
    ) == "REJECTED"
