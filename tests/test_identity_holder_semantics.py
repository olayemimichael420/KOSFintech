from identity_holder_semantics import (
    IdentityHolderSemanticValidator,
    IdentityRecord,
    SemanticResult,
)


def subject(entity_id="PERSON-001", classification="PERSON"):
    return IdentityRecord(entity_id, "SUBJECT", classification)


def office(entity_id="OFFICE-001"):
    return IdentityRecord(entity_id, "OFFICE", "INSTITUTIONAL_OFFICE")


def authority(entity_id="AUTH-001"):
    return IdentityRecord(entity_id, "AUTHORITY", "DELEGATED_AUTHORITY")


def action(entity_id="ACTION-001"):
    return IdentityRecord(entity_id, "ACTION", "OPERATION")


def test_r4_subject_holds_authority_is_valid():
    result = IdentityHolderSemanticValidator().validate("HOLDS", subject(), authority())
    assert result.result is SemanticResult.VALID


def test_r4_subject_occupies_office_is_valid():
    result = IdentityHolderSemanticValidator().validate("OCCUPIES", subject(), office())
    assert result.result is SemanticResult.VALID


def test_r4_subject_performs_action_is_valid():
    result = IdentityHolderSemanticValidator().validate("PERFORMS", subject(), action())
    assert result.result is SemanticResult.VALID


def test_r4_office_cannot_be_subject_holder_of_authority():
    result = IdentityHolderSemanticValidator().validate("HOLDS", office(), authority())
    assert result.result is SemanticResult.INVALID


def test_r4_authority_cannot_occupy_office_as_identity():
    result = IdentityHolderSemanticValidator().validate("OCCUPIES", authority(), office())
    assert result.result is SemanticResult.INVALID


def test_r4_office_cannot_perform_action_as_person_identity():
    result = IdentityHolderSemanticValidator().validate("PERFORMS", office(), action())
    assert result.result is SemanticResult.INVALID


def test_r4_unknown_holder_relation_is_indeterminate():
    result = IdentityHolderSemanticValidator().validate("UNKNOWN", subject(), authority())
    assert result.result is SemanticResult.INDETERMINATE
