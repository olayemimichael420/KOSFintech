from dsl_ir_v2 import (
    EstablishmentIR,
    NonEstablishmentConstraintIR,
    PreservationConstraintIR,
    PropositionIR,
    RequirementIR,
    parse_to_ir,
    PreservationKind,
    BoundaryResolutionContext,
    CompiledPreservationIR,
    resolve_boundaries,
    compile_preservations,
)
from tests.test_dsl_parser_v1 import SESSION_TEACHER_PREACHER_ASSIGNMENT, TEACHING_SUBJECT


def test_v2_typed_ir_preserves_declared_structure():
    ir = parse_to_ir(TEACHING_SUBJECT)

    assert ir.name == "TeachingSubject"
    assert isinstance(ir.proposition, PropositionIR)
    assert isinstance(ir.requires[0], RequirementIR)
    assert isinstance(ir.establishes[0], EstablishmentIR)
    assert isinstance(ir.preserves[0], PreservationConstraintIR)
    assert isinstance(ir.does_not_establish[0], NonEstablishmentConstraintIR)


def test_v2_typed_ir_does_not_invent_missing_semantics():
    source = """DECLARATION Minimal
PROPOSITION "A bounded proposition."
END
"""

    ir = parse_to_ir(source)

    assert ir.requires == ()
    assert ir.establishes == ()
    assert ir.preserves == ()
    assert ir.does_not_establish == ()


def test_v2_boundary_constraint_connects_to_preservation_mechanism():
    from p3_relation_algebra import Boundary, Fact, Relation
    from p4_boundary_transform import (
        BoundaryCorrespondence,
        Transformation,
        TransformationKind,
        evaluate_correspondence,
        transform_boundaries,
        transform_facts,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    constraint = next(item for item in ir.preserves if item.kind.value == "BOUNDARY")
    assert constraint.value == "tenant boundary"

    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")
    source_boundary = resolve_boundaries(ir, context)[0]
    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    target_boundary = next(iter(transform_boundaries([source_boundary], transformation)))
    target_facts = transform_facts(source_facts, transformation)

    correspondence = BoundaryCorrespondence(source_boundary, target_boundary)

    assert evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope="tenant",
    ) == "PRESERVED"



def test_boundary_constraint_resolves_through_explicit_context():
    from p3_relation_algebra import Boundary

    ir = parse_to_ir(TEACHING_SUBJECT)
    constraint = next(
        item for item in ir.preserves
        if item.kind is PreservationKind.BOUNDARY
    )
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")

    assert context.resolve(constraint) == Boundary(
        "TenantA", "TenantB", scope="tenant"
    )



def test_resolve_boundaries_ignores_unresolved_constraints():
    ir = parse_to_ir(SESSION_TEACHER_PREACHER_ASSIGNMENT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")

    assert resolve_boundaries(ir, context) == ()


def test_resolve_boundaries_compiles_typed_boundary_constraints():
    from p3_relation_algebra import Boundary

    ir = parse_to_ir(TEACHING_SUBJECT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")

    assert resolve_boundaries(ir, context) == (
        Boundary("TenantA", "TenantB", scope="tenant"),
    )



def test_dsl_derived_boundary_rejects_endpoint_collapse():
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind, transform_boundaries, transform_facts

    ir = parse_to_ir(TEACHING_SUBJECT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")
    boundaries = resolve_boundaries(ir, context)
    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantX")),
    )

    import pytest
    with pytest.raises(ValueError, match="boundary endpoint collapse"):
        transform_boundaries(boundaries, transformation)

    transform_facts(source_facts, transformation)



def test_dsl_derived_boundary_detects_semantic_violation():
    from p3_relation_algebra import Fact, Relation, Conformance
    from p4_boundary_transform import Transformation, TransformationKind, verify_preservation

    ir = parse_to_ir(TEACHING_SUBJECT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")
    boundaries = resolve_boundaries(ir, context)
    facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    result = verify_preservation(
        boundaries,
        facts,
        Transformation(
            TransformationKind.REBIND,
            (("TenantB", "TenantC"),),
        ),
        scope="tenant",
    )

    assert result.before is Conformance.CONFLICT
    assert result.after is Conformance.ALLOW
    assert result.preserved is False



def test_compiled_preservation_retains_constraint_and_boundary():
    from p3_relation_algebra import Boundary

    ir = parse_to_ir(TEACHING_SUBJECT)
    constraint = next(
        item for item in ir.preserves
        if item.kind is PreservationKind.BOUNDARY
    )
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")
    boundary = context.resolve(constraint)
    compiled = CompiledPreservationIR(constraint, boundary)

    assert compiled.constraint is constraint
    assert compiled.boundary == Boundary("TenantA", "TenantB", scope="tenant")



def test_compile_preservations_retains_constraint_boundary_pair():
    from p3_relation_algebra import Boundary

    ir = parse_to_ir(TEACHING_SUBJECT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")
    compiled = compile_preservations(ir, context)

    assert len(compiled) == 1
    assert compiled[0].constraint.value == "tenant boundary"
    assert compiled[0].constraint.kind is PreservationKind.BOUNDARY
    assert compiled[0].boundary == Boundary("TenantA", "TenantB", scope="tenant")



def test_compile_preservations_does_not_promote_unresolved_constraints():
    ir = parse_to_ir(SESSION_TEACHER_PREACHER_ASSIGNMENT)
    context = BoundaryResolutionContext("TenantA", "TenantB", "tenant")

    assert compile_preservations(ir, context) == ()

def test_dsl_compiled_boundary_correspondence_preserves_semantics():
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import (
        Transformation,
        TransformationKind,
        establish_correspondence,
        evaluate_correspondence,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )
    compiled_boundary = compiled[0].boundary

    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    target_facts = (
        Fact("TenantX", Relation.EQUIVALENT, "TenantY", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    correspondence = establish_correspondence(
        compiled_boundary,
        transformation,
    )

    assert evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope="tenant",
    ) == "PRESERVED"

def test_dsl_compiled_boundary_correspondence_detects_violation():
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import (
        Transformation,
        TransformationKind,
        establish_correspondence,
        evaluate_correspondence,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )
    compiled_boundary = compiled[0].boundary

    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    target_facts = (
        Fact("TenantX", Relation.OWNS, "TenantY", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    correspondence = establish_correspondence(
        compiled_boundary,
        transformation,
    )

    assert evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope="tenant",
    ) == "VIOLATED"

def test_dsl_ir_end_to_end_transformation_preserves_boundary_semantics():
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import (
        Transformation,
        TransformationKind,
        establish_correspondence,
        evaluate_correspondence,
        transform_facts,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )
    source_boundary = compiled[0].boundary
    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    correspondence = establish_correspondence(source_boundary, transformation)
    target_facts = transform_facts(source_facts, transformation)

    assert evaluate_correspondence(
        correspondence,
        source_facts,
        target_facts,
        scope="tenant",
    ) == "PRESERVED"


def test_dsl_ir_end_to_end_adversarial_transformation_detects_violation():
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import (
        Transformation,
        TransformationKind,
        establish_correspondence,
        evaluate_correspondence,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )
    source_boundary = compiled[0].boundary
    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    correspondence = establish_correspondence(source_boundary, transformation)
    adversarial_target_facts = (
        Fact("TenantX", Relation.OWNS, "TenantY", scope="tenant"),
    )

    assert evaluate_correspondence(
        correspondence,
        source_facts,
        adversarial_target_facts,
        scope="tenant",
    ) == "VIOLATED"


def test_dsl_boundary_pipeline_evaluates_compiled_transformation():
    from p3_relation_algebra import Fact, Relation
    from dsl_boundary_pipeline_v1 import evaluate_compiled_transformation
    from p4_boundary_transform import Transformation, TransformationKind

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]
    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert evaluate_compiled_transformation(
        compiled,
        source_facts,
        transformation,
        scope="tenant",
    ) == "PRESERVED"


def test_dsl_boundary_pipeline_composed_transformations_preserve_boundary():
    from dsl_boundary_pipeline_v1 import evaluate_compiled_transformation
    from p4_boundary_transform import Transformation, TransformationKind, transform_facts
    from p3_relation_algebra import Fact, Relation

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )

    first = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    second = Transformation(
        TransformationKind.RENAME,
        (("TenantX", "TenantM"), ("TenantY", "TenantN")),
    )

    intermediate_facts = transform_facts(source_facts, first)
    final_facts = transform_facts(intermediate_facts, second)

    assert final_facts == (
        Fact("TenantM", Relation.EQUIVALENT, "TenantN", scope="tenant"),
    )

    composed = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantM"), ("TenantB", "TenantN")),
    )

    assert evaluate_compiled_transformation(
        compiled,
        source_facts,
        composed,
        scope="tenant",
    ) == "PRESERVED"


def test_dsl_boundary_pipeline_v2_fixed_boundary_detects_rebind_violation():
    from dsl_boundary_pipeline_v2 import evaluate_protected_transformation
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    transformation = Transformation(
        TransformationKind.REBIND,
        (("TenantB", "TenantC"),),
    )

    assert evaluate_protected_transformation(
        compiled,
        source_facts,
        transformation,
        scope="tenant",
    ) == "VIOLATED"


def test_dsl_boundary_pipeline_v1_characterizes_moving_boundary_limitation():
    from dsl_boundary_pipeline_v1 import evaluate_compiled_transformation
    from p4_boundary_transform import Transformation, TransformationKind, transform_facts
    from p3_relation_algebra import Fact, Relation

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    first = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    intermediate_facts = transform_facts(source_facts, first)

    second = Transformation(
        TransformationKind.REBIND,
        (("TenantY", "TenantZ"),),
    )

    assert evaluate_compiled_transformation(
        compiled,
        intermediate_facts,
        second,
        scope="tenant",
    ) == "PRESERVED"

def test_dsl_boundary_pipeline_rejects_endpoint_collapse():
    import pytest
    from p3_relation_algebra import Fact, Relation
    from dsl_boundary_pipeline_v1 import evaluate_compiled_transformation
    from p4_boundary_transform import Transformation, TransformationKind

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]
    source_facts = (
        Fact("TenantA", Relation.EQUIVALENT, "TenantB", scope="tenant"),
    )
    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantX")),
    )

    with pytest.raises(
        ValueError,
        match="boundary endpoint collapse is not boundary-preserving",
    ):
        evaluate_compiled_transformation(
            compiled,
            source_facts,
            transformation,
            scope="tenant",
        )


def test_dsl_compiled_boundary_rejects_endpoint_collapse():
    import pytest
    from p4_boundary_transform import (
        Transformation,
        TransformationKind,
        transform_boundaries,
    )

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )
    compiled_boundary = compiled[0].boundary

    transformation = Transformation(
        TransformationKind.RENAME,
        (("TenantA", "TenantX"), ("TenantB", "TenantX")),
    )

    with pytest.raises(
        ValueError,
        match="boundary endpoint collapse is not boundary-preserving",
    ):
        transform_boundaries((compiled_boundary,), transformation)


def test_dsl_boundary_pipeline_v4_unresolved_compatibility_is_not_preserved():
    from dsl_boundary_pipeline_v4 import evaluate_validated_transformation
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    transformation = Transformation(TransformationKind.CANONICALIZE)

    assert evaluate_validated_transformation(
        compiled,
        source_facts,
        transformation,
        scope="tenant",
    ) == "VIOLATED"


def test_dsl_boundary_pipeline_v4_late_incompatible_stage_is_detected():
    from dsl_boundary_pipeline_v4 import evaluate_validated_transformation
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind, transform_facts

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
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

    intermediate_facts = transform_facts(source_facts, rename)

    assert evaluate_validated_transformation(
        compiled,
        intermediate_facts,
        rebind,
        scope="tenant",
    ) == "VIOLATED"


def test_dsl_boundary_pipeline_v4_later_rename_does_not_repair_prior_rebind():
    from dsl_boundary_pipeline_v4 import evaluate_validated_transformation
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind, transform_facts

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    rebind = Transformation(
        TransformationKind.REBIND,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )
    rename = Transformation(
        TransformationKind.RENAME,
        (("TenantX", "TenantP"), ("TenantY", "TenantQ")),
    )

    intermediate_facts = transform_facts(source_facts, rebind)

    assert evaluate_validated_transformation(
        compiled,
        intermediate_facts,
        rename,
        scope="tenant",
    ) == "VIOLATED"


def test_dsl_boundary_pipeline_v4_complete_rebind_is_not_semantically_preserving():
    from dsl_boundary_pipeline_v4 import evaluate_validated_transformation
    from p3_relation_algebra import Fact, Relation
    from p4_boundary_transform import Transformation, TransformationKind

    ir = parse_to_ir(TEACHING_SUBJECT)
    compiled = compile_preservations(
        ir,
        BoundaryResolutionContext("TenantA", "TenantB", "tenant"),
    )[0]

    source_facts = (
        Fact("TenantA", Relation.SAME_AS, "TenantB", scope="tenant"),
    )

    transformation = Transformation(
        TransformationKind.REBIND,
        (("TenantA", "TenantX"), ("TenantB", "TenantY")),
    )

    assert evaluate_validated_transformation(
        compiled,
        source_facts,
        transformation,
        scope="tenant",
    ) == "VIOLATED"
