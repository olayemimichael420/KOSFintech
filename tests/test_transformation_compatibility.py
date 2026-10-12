from dsl_ir_v2 import PreservationConstraintIR, PreservationKind
from p4_boundary_transform import Transformation, TransformationKind
from transformation_compatibility import TransformationCompatibilityContract, transformation_preserves_constraint
from transformation_composition import compose_transformations


def test_tenant_boundary_allows_rename():
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    assert transformation_preserves_constraint(constraint, transformation) is True


def test_tenant_boundary_rejects_rebind():
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    transformation = Transformation(
        TransformationKind.REBIND,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    assert transformation_preserves_constraint(constraint, transformation) is False


def test_unmodeled_transformation_remains_unresolved():
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    transformation = Transformation(TransformationKind.CANONICALIZE)
    assert transformation_preserves_constraint(constraint, transformation) is None


def test_unmodeled_preservation_constraint_is_not_compatible():
    constraint = PreservationConstraintIR(
        "scope isolation",
        PreservationKind.UNRESOLVED,
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    assert transformation_preserves_constraint(constraint, transformation) is None


def test_transformation_chain_preserves_explicit_stage_order():
    from p3_relation_algebra import Fact, Relation
    from transformation_composition import compose_transformations

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(rename, rebind)

    assert chain.stages == (rename, rebind)
    assert chain.apply(facts) == (
        Fact("TenantP", Relation.SAME_AS, "TenantQ", scope="tenant"),
    )


def test_transformation_chain_rejects_late_incompatible_stage():
    from transformation_composition import chain_preserves_constraint, compose_transformations

    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(rename, rebind)

    assert chain_preserves_constraint(constraint, chain) is False


def test_transformation_chain_rejects_early_incompatible_stage():
    from transformation_composition import chain_preserves_constraint, compose_transformations

    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(rebind, rename)

    assert chain_preserves_constraint(constraint, chain) is False


def test_transformation_chain_rejects_unresolved_stage():
    from transformation_composition import chain_preserves_constraint, compose_transformations

    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    canonicalize = Transformation(TransformationKind.CANONICALIZE)

    chain = compose_transformations(rename, canonicalize)

    assert chain_preserves_constraint(constraint, chain) is False


def test_structural_and_semantic_compatibility_are_independent_for_rebind():
    from boundary_correspondence_validation import validate_boundary_correspondence
    from p3_relation_algebra import Boundary
    from p4_boundary_transform import establish_correspondence
    from structural_transformation_compatibility import structurally_compatible_boundary

    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    boundary = Boundary("TenantA", "TenantB", "tenant")
    transformation = Transformation(
        TransformationKind.REBIND,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    correspondence = establish_correspondence(boundary, transformation)

    assert validate_boundary_correspondence(
        correspondence.source,
        correspondence.target,
        transformation,
    ) is True
    assert structurally_compatible_boundary(boundary, transformation) is True
    assert transformation_preserves_constraint(constraint, transformation) is False


def test_structural_compatibility_survives_chain_while_semantic_compatibility_fails_late():
    from p3_relation_algebra import Boundary
    from structural_transformation_compatibility import structurally_compatible_boundary

    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    boundary = Boundary("TenantA", "TenantB", "tenant")

    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    next_boundary = Boundary("TenantX", "TenantY", "tenant")

    assert structurally_compatible_boundary(boundary, rename) is True
    assert transformation_preserves_constraint(constraint, rename) is True
    assert structurally_compatible_boundary(next_boundary, rebind) is True
    assert transformation_preserves_constraint(constraint, rebind) is False


def test_end_to_end_composed_rename_chain_is_preserved():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import (
        compose_transformations,
        evaluate_chain_preservation,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    rename1 = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rename2 = Transformation(
        TransformationKind.RENAME,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(rename1, rename2)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "PRESERVED"


def test_end_to_end_composed_rename_rebind_chain_is_violated():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import (
        compose_transformations,
        evaluate_chain_preservation,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(rename, rebind)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "VIOLATED"


def test_end_to_end_composed_rename_canonicalize_chain_is_violated():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import (
        compose_transformations,
        evaluate_chain_preservation,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    canonicalize = Transformation(TransformationKind.CANONICALIZE)

    chain = compose_transformations(rename, canonicalize)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "VIOLATED"


def test_end_to_end_compatible_rename_with_partial_boundary_mapping_is_violated():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import (
        compose_transformations,
        evaluate_chain_preservation,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    partial_rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"),),
    )

    chain = compose_transformations(partial_rename)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "VIOLATED"


def test_end_to_end_compatible_rename_with_endpoint_collapse_is_violated():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import (
        compose_transformations,
        evaluate_chain_preservation,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    collapsing_rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantX")),
    )

    chain = compose_transformations(collapsing_rename)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "VIOLATED"


def test_boundary_correspondence_rejects_scope_change_with_complete_mapping():
    from boundary_correspondence_validation import validate_boundary_correspondence
    from p3_relation_algebra import Boundary
    from p4_boundary_transform import Transformation, TransformationKind

    source = Boundary("TenantA", "TenantB", scope="tenant")
    target = Boundary("TenantX", "TenantY", scope="global")
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert not validate_boundary_correspondence(
        source,
        target,
        rename,
    )


def test_boundary_correspondence_accepts_complete_mapping_same_scope():
    from boundary_correspondence_validation import validate_boundary_correspondence
    from p3_relation_algebra import Boundary
    from p4_boundary_transform import Transformation, TransformationKind

    source = Boundary("TenantA", "TenantB", scope="tenant")
    target = Boundary("TenantX", "TenantY", scope="tenant")
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert validate_boundary_correspondence(
        source,
        target,
        rename,
    )


def test_scope_isolation_rename_compatibility_is_currently_unresolved():
    constraint = PreservationConstraintIR(
        "scope isolation",
        PreservationKind.UNRESOLVED,
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert transformation_preserves_constraint(constraint, transformation) is None


def test_unresolved_same_value_does_not_inherit_typed_boundary_rule():
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.UNRESOLVED)
    transformation = Transformation(TransformationKind.RENAME)
    assert transformation_preserves_constraint(constraint, transformation) is None



def test_contract_explicitly_compatible_returns_true():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary", compatible_transformations=frozenset({TransformationKind.RENAME}))
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    assert contract.evaluate(constraint, Transformation(TransformationKind.RENAME)) is True


def test_contract_explicitly_incompatible_returns_false():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary", incompatible_transformations=frozenset({TransformationKind.REBIND}))
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    assert contract.evaluate(constraint, Transformation(TransformationKind.REBIND)) is False


def test_contract_unmodeled_transformation_returns_none():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary", compatible_transformations=frozenset({TransformationKind.RENAME}))
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    assert contract.evaluate(constraint, Transformation(TransformationKind.CANONICALIZE)) is None


def test_contract_different_preservation_kind_returns_none():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary", compatible_transformations=frozenset({TransformationKind.RENAME}))
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.UNRESOLVED)
    assert contract.evaluate(constraint, Transformation(TransformationKind.RENAME)) is None


def test_contract_different_preservation_value_returns_none():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary", compatible_transformations=frozenset({TransformationKind.RENAME}))
    constraint = PreservationConstraintIR("other boundary", PreservationKind.BOUNDARY)
    assert contract.evaluate(constraint, Transformation(TransformationKind.RENAME)) is None


def test_empty_contract_declares_no_compatibility():
    contract = TransformationCompatibilityContract(PreservationKind.BOUNDARY, "tenant boundary")
    constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    assert contract.evaluate(constraint, Transformation(TransformationKind.RENAME)) is None



def test_independent_contract_can_define_different_compatibility():
    scope_contract = TransformationCompatibilityContract(
        PreservationKind.UNRESOLVED,
        "scope isolation",
        compatible_transformations=frozenset({TransformationKind.REBIND}),
    )
    constraint = PreservationConstraintIR("scope isolation", PreservationKind.UNRESOLVED)
    assert scope_contract.evaluate(constraint, Transformation(TransformationKind.REBIND)) is True


def test_independent_contract_does_not_change_tenant_boundary_policy():
    scope_contract = TransformationCompatibilityContract(
        PreservationKind.UNRESOLVED,
        "scope isolation",
        compatible_transformations=frozenset({TransformationKind.REBIND}),
    )
    scope_constraint = PreservationConstraintIR("scope isolation", PreservationKind.UNRESOLVED)
    tenant_constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    rebind = Transformation(TransformationKind.REBIND)
    assert scope_contract.evaluate(scope_constraint, rebind) is True
    assert scope_contract.evaluate(tenant_constraint, rebind) is None
    assert transformation_preserves_constraint(tenant_constraint, rebind) is False


def test_independent_contracts_can_return_different_answers_for_same_transformation():
    rename_contract = TransformationCompatibilityContract(
        PreservationKind.BOUNDARY,
        "tenant boundary",
        compatible_transformations=frozenset({TransformationKind.RENAME}),
    )
    rebind_contract = TransformationCompatibilityContract(
        PreservationKind.UNRESOLVED,
        "scope isolation",
        compatible_transformations=frozenset({TransformationKind.REBIND}),
    )
    tenant_constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    scope_constraint = PreservationConstraintIR("scope isolation", PreservationKind.UNRESOLVED)
    rebind = Transformation(TransformationKind.REBIND)
    assert rename_contract.evaluate(tenant_constraint, rebind) is None
    assert rebind_contract.evaluate(scope_constraint, rebind) is True



def test_independent_contracts_remain_isolated_across_a_chain():
    rename_contract = TransformationCompatibilityContract(
        PreservationKind.BOUNDARY,
        "tenant boundary",
        compatible_transformations=frozenset({TransformationKind.RENAME}),
    )
    rebind_contract = TransformationCompatibilityContract(
        PreservationKind.UNRESOLVED,
        "scope isolation",
        compatible_transformations=frozenset({TransformationKind.REBIND}),
    )
    tenant_constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    scope_constraint = PreservationConstraintIR("scope isolation", PreservationKind.UNRESOLVED)
    chain = compose_transformations(
        Transformation(TransformationKind.RENAME),
        Transformation(TransformationKind.REBIND),
    )
    assert [rename_contract.evaluate(tenant_constraint, stage) for stage in chain.stages] == [True, None]
    assert [rebind_contract.evaluate(scope_constraint, stage) for stage in chain.stages] == [None, True]


def test_chain_stage_order_does_not_cross_contaminate_contract_results():
    first_contract = TransformationCompatibilityContract(
        PreservationKind.BOUNDARY,
        "tenant boundary",
        compatible_transformations=frozenset({TransformationKind.RENAME}),
        incompatible_transformations=frozenset({TransformationKind.REBIND}),
    )
    second_contract = TransformationCompatibilityContract(
        PreservationKind.UNRESOLVED,
        "scope isolation",
        compatible_transformations=frozenset({TransformationKind.REBIND}),
        incompatible_transformations=frozenset({TransformationKind.RENAME}),
    )
    tenant_constraint = PreservationConstraintIR("tenant boundary", PreservationKind.BOUNDARY)
    scope_constraint = PreservationConstraintIR("scope isolation", PreservationKind.UNRESOLVED)
    chain = compose_transformations(
        Transformation(TransformationKind.RENAME),
        Transformation(TransformationKind.REBIND),
    )
    first_results = [first_contract.evaluate(tenant_constraint, stage) for stage in chain.stages]
    second_results = [second_contract.evaluate(scope_constraint, stage) for stage in chain.stages]
    assert first_results == [True, False]
    assert second_results == [False, True]



def test_p9_two_stage_compatible_chain_preserves_boundary():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import compose_transformations, evaluate_chain_preservation

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    first = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    second = Transformation(
        TransformationKind.RENAME,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(first, second)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "PRESERVED"


def test_p9_structurally_valid_but_semantically_incompatible_stage_is_rejected():
    from dsl_ir_v2 import BoundaryResolutionContext, compile_preservations, parse_to_ir
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind
    from tests.test_dsl_parser_v1 import TEACHING_SUBJECT
    from transformation_composition import compose_transformations, evaluate_chain_preservation

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    first = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    second = Transformation(
        TransformationKind.REBIND,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    chain = compose_transformations(first, second)

    assert evaluate_chain_preservation(
        compiled,
        facts,
        chain,
        scope="tenant",
    ) == "VIOLATED"


def test_structural_compatibility_generalizes_across_boundary_instances():
    from p3_relation_algebra import Boundary
    from p4_boundary_transform import Transformation, TransformationKind
    from structural_transformation_compatibility import structurally_compatible_boundary

    cases = [
        (Boundary("TenantA", "TenantB", "tenant"), "TenantA", "TenantX", "TenantB", "TenantY"),
        (Boundary("CustomerA", "CustomerB", "customer"), "CustomerA", "CustomerX", "CustomerB", "CustomerY"),
        (Boundary("SchoolA", "SchoolB", "school"), "SchoolA", "SchoolX", "SchoolB", "SchoolY"),
    ]

    for boundary, left, left_target, right, right_target in cases:
        transformation = Transformation(
            TransformationKind.RENAME,
            ((left, left_target), (right, right_target)),
        )
        assert structurally_compatible_boundary(boundary, transformation)


def test_structural_compatibility_rejects_partial_mapping_across_boundary_instances():
    from p3_relation_algebra import Boundary
    from p4_boundary_transform import Transformation, TransformationKind
    from structural_transformation_compatibility import structurally_compatible_boundary

    cases = [
        (Boundary("TenantA", "TenantB", "tenant"), "TenantA", "TenantX"),
        (Boundary("CustomerA", "CustomerB", "customer"), "CustomerA", "CustomerX"),
        (Boundary("SchoolA", "SchoolB", "school"), "SchoolA", "SchoolX"),
    ]

    for boundary, left, left_target in cases:
        transformation = Transformation(
            TransformationKind.RENAME,
            ((left, left_target),),
        )
        assert not structurally_compatible_boundary(boundary, transformation)
