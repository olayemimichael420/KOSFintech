"""P3 relation-algebra acceptance matrix.

These tests intentionally target the isolated prototype, not dsl_parser_v1.py.
"""

from p3_relation_algebra import (
    Boundary,
    BoundaryLedger,
    Conformance,
    Fact,
    Relation,
    ScopeTransition,
    evaluate,
    promotion_path_exists,
)


def test_p3_01_equivalent_symmetry_blocks():
    boundary = [Boundary("A", "B")]
    facts = [Fact("B", Relation.EQUIVALENT, "A")]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.CONFLICT


def test_p3_02_may_grant_is_asymmetric():
    facts = [Fact("B", Relation.MAY_GRANT, "A")]
    assert not promotion_path_exists(facts, "A", "B", scope="S")
    assert not promotion_path_exists(facts, "B", "A", scope="S")


def test_p3_03_equivalent_transitivity_blocks():
    boundary = [Boundary("A", "C")]
    facts = [
        Fact("A", Relation.EQUIVALENT, "B"),
        Fact("B", Relation.EQUIVALENT, "C"),
    ]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.CONFLICT


def test_p3_04_may_grant_is_not_promotion_transitive():
    boundary = [Boundary("A", "C")]
    facts = [
        Fact("A", Relation.MAY_GRANT, "B"),
        Fact("B", Relation.MAY_GRANT, "C"),
    ]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.ALLOW


def test_p3_05_mixed_relations_do_not_promote():
    boundary = [Boundary("A", "C")]
    facts = [
        Fact("A", Relation.EQUIVALENT, "B"),
        Fact("B", Relation.MAY_GRANT, "C"),
    ]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.ALLOW

    facts = [
        Fact("A", Relation.MAY_GRANT, "B"),
        Fact("B", Relation.EQUIVALENT, "C"),
    ]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.ALLOW


def test_p3_06_owns_chain_does_not_promote():
    boundary = [Boundary("A", "C")]
    facts = [
        Fact("A", Relation.OWNS, "B"),
        Fact("B", Relation.OWNS, "C"),
    ]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.ALLOW


def test_p3_07_reversed_boundary_normalizes_identically():
    assert Boundary("A", "B").normalized() == Boundary("B", "A").normalized()


def test_p3_08_duplicate_boundaries_normalize_to_one_commitment():
    ledger = BoundaryLedger([
        Boundary("A", "B"),
        Boundary("A", "B"),
        Boundary("B", "A"),
    ])
    assert len(ledger) == 1


def test_p3_09_contradictory_boundary_is_fail_closed():
    boundary = [Boundary("A", "B")]
    facts = [Fact("A", Relation.IDENTITY, "B")]
    assert evaluate(boundary, facts, source_scope="S") is Conformance.CONFLICT


def test_p3_10_independent_scopes_are_independent():
    boundary = [Boundary("A", "B", scope="DOMAIN_A")]
    facts = [Fact("A", Relation.EQUIVALENT, "B", scope="DOMAIN_B")]
    assert evaluate(boundary, facts, source_scope="DOMAIN_A") is Conformance.ALLOW


def test_p3_11_unauthorized_cross_scope_import_is_blocked():
    boundary = [Boundary("A", "B", scope="DOMAIN_A")]
    facts = [Fact("A", Relation.EQUIVALENT, "B", scope="DOMAIN_B")]
    assert evaluate(
        boundary,
        facts,
        source_scope="DOMAIN_A",
        target_scope="DOMAIN_B",
    ) is Conformance.SCOPE_VIOLATION


def test_p3_12_permitted_scope_transition_is_evaluated():
    boundary = [Boundary("A", "B", scope="DOMAIN_B")]
    facts = [Fact("A", Relation.EQUIVALENT, "B", scope="DOMAIN_B")]
    transition = ScopeTransition("DOMAIN_A", "DOMAIN_B", permitted=True)
    assert evaluate(
        boundary,
        facts,
        source_scope="DOMAIN_A",
        target_scope="DOMAIN_B",
        transition=transition,
    ) is Conformance.EVALUATE
