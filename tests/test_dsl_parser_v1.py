from dsl_parser_v1 import SemanticDeclaration, parse_declaration, render_declaration


SERVICE_ACT = """DECLARATION ServiceActCompletion
PROPOSITION "A submitted ServiceAct may be completed when its verification outcome is APPROVED."
REQUIRES "tenant-scoped ServiceAct"
REQUIRES "verification outcome"
ESTABLISHES "completion of the submitted ServiceAct"
PRESERVES "individual verification determinations"
DOES_NOT_ESTABLISH "constitutional authority"
DOES_NOT_ESTABLISH "universal proof"
DOES_NOT_ESTABLISH "Talent Point eligibility"
END
"""


TEACHING_SUBJECT = """DECLARATION TeachingSubject
PROPOSITION "TeachingSubject represents a reusable tenant-scoped teaching subject identity."
REQUIRES "tenant scope"
REQUIRES "subject identity"
ESTABLISHES "teaching subject identity"
PRESERVES "tenant boundary"
DOES_NOT_ESTABLISH "teaching capacity"
DOES_NOT_ESTABLISH "assignment"
DOES_NOT_ESTABLISH "attendance"
DOES_NOT_ESTABLISH "ecclesiastical authority"
DOES_NOT_ESTABLISH "application authorization"
END
"""


SESSION_TEACHER_PREACHER_ASSIGNMENT = """DECLARATION SessionTeacherPreacherAssignment
PROPOSITION "SessionTeacherPreacherAssignment represents a tenant-scoped relationship between an existing TeacherPreacher capacity and an existing TeachingSession."
REQUIRES "tenant scope"
REQUIRES "TeacherPreacher capacity"
REQUIRES "TeachingSession"
ESTABLISHES "TeacherPreacher-to-TeachingSession assignment"
PRESERVES "active | inactive state representation"
PRESERVES "tenant-scoped foreign-key integrity"
DOES_NOT_ESTABLISH "membership"
DOES_NOT_ESTABLISH "authentication"
DOES_NOT_ESTABLISH "ecclesiastical authority"
DOES_NOT_ESTABLISH "participation"
DOES_NOT_ESTABLISH "attendance"
DOES_NOT_ESTABLISH "learning"
DOES_NOT_ESTABLISH "assessment"
DOES_NOT_ESTABLISH "result"
DOES_NOT_ESTABLISH "progress"
DOES_NOT_ESTABLISH "application authorization merely from the assignment relationship"
END
"""


def test_parser_v1_reuses_the_same_semantic_shape():
    service_act = parse_declaration(SERVICE_ACT)
    teaching_subject = parse_declaration(TEACHING_SUBJECT)

    assert service_act.name == "ServiceActCompletion"
    assert teaching_subject.name == "TeachingSubject"

    assert service_act.proposition
    assert teaching_subject.proposition

    assert service_act.requires
    assert teaching_subject.requires

    assert service_act.establishes
    assert teaching_subject.establishes

    assert service_act.preserves
    assert teaching_subject.preserves

    assert service_act.does_not_establish
    assert teaching_subject.does_not_establish


def test_parser_v1_handles_session_teacher_preacher_assignment_without_expansion():
    parsed = parse_declaration(SESSION_TEACHER_PREACHER_ASSIGNMENT)

    assert parsed.name == "SessionTeacherPreacherAssignment"
    assert "TeacherPreacher capacity" in parsed.requires
    assert "TeachingSession" in parsed.requires
    assert "TeacherPreacher-to-TeachingSession assignment" in parsed.establishes
    assert "active | inactive state representation" in parsed.preserves
    assert "ecclesiastical authority" in parsed.does_not_establish
    assert "application authorization merely from the assignment relationship" in parsed.does_not_establish


def test_parser_v1_is_lossless_for_the_declared_structure():
    source = SESSION_TEACHER_PREACHER_ASSIGNMENT
    parsed = parse_declaration(source)
    assert parse_declaration(render_declaration(parsed)) == parsed


def test_parser_v1_does_not_infer_missing_semantics():
    source = """DECLARATION Minimal
PROPOSITION "A bounded proposition."
END
"""
    parsed = parse_declaration(source)

    assert parsed.requires == ()
    assert parsed.establishes == ()
    assert parsed.preserves == ()
    assert parsed.does_not_establish == ()


def test_parser_v1_rejects_unknown_fields():
    source = """DECLARATION Invalid
PROPOSITION "A bounded proposition."
AUTHORITY "not a supported field"
END
"""
    try:
        parse_declaration(source)
        assert False, "unknown fields must be rejected"
    except ValueError as exc:
        assert "unsupported declaration field" in str(exc)
