from visioneer_semantics import (
    FoundingAuthorityReference,
    SemanticResult,
    VisioneerSemanticValidator,
    VisioneerSubject,
)


def subject(**overrides):
    values = {
        "subject_id": "PERSON-VISIONEER",
        "entity_type": "SUBJECT",
        "classification": "VISIONEER",
    }
    values.update(overrides)
    return VisioneerSubject(**values)


def authority(**overrides):
    values = {
        "authority_id": "AUTH-FOUNDING",
        "holder_id": "PERSON-VISIONEER",
        "status": "ACTIVE",
        "powers": frozenset({"ESTABLISH_OFFICE"}),
        "provenance": "FOUNDING-BASIS-001",
    }
    values.update(overrides)
    return FoundingAuthorityReference(**values)


def test_visioneer_is_subject_not_authority_type():
    result = VisioneerSemanticValidator().validate_subject(subject())
    assert result.result is SemanticResult.VALID


def test_visioneer_cannot_be_retyped_as_authority():
    result = VisioneerSemanticValidator().validate_subject(
        subject(entity_type="AUTHORITY")
    )
    assert result.result is SemanticResult.INVALID


def test_visioneer_classification_alone_does_not_create_authority():
    result = VisioneerSemanticValidator().validate_authority_holder(
        subject(),
        authority(status="PROPOSED"),
    )
    assert result.result is SemanticResult.INVALID


def test_visioneer_may_hold_separately_represented_founding_authority():
    result = VisioneerSemanticValidator().validate_authority_holder(
        subject(), authority()
    )
    assert result.result is SemanticResult.VALID


def test_authority_must_name_the_visioneer_as_holder():
    result = VisioneerSemanticValidator().validate_authority_holder(
        subject(), authority(holder_id="OTHER-SUBJECT")
    )
    assert result.result is SemanticResult.INVALID


def test_founding_authority_requires_independent_provenance():
    result = VisioneerSemanticValidator().validate_authority_holder(
        subject(), authority(provenance="")
    )
    assert result.result is SemanticResult.INVALID
