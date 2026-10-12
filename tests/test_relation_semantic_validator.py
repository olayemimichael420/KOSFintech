from relation_semantic_validator import RelationSemanticValidator, SemanticResult


def test_r2_holds_subject_to_authority_is_valid():
    result = RelationSemanticValidator().validate("HOLDS", "SUBJECT", "AUTHORITY")
    assert result.result is SemanticResult.VALID


def test_r2_occupies_subject_to_office_is_valid():
    result = RelationSemanticValidator().validate("OCCUPIES", "SUBJECT", "OFFICE")
    assert result.result is SemanticResult.VALID


def test_r2_constitutes_authority_to_office_is_valid():
    result = RelationSemanticValidator().validate("CONSTITUTES", "AUTHORITY", "OFFICE")
    assert result.result is SemanticResult.VALID


def test_r2_authorizes_subject_to_action_is_invalid():
    result = RelationSemanticValidator().validate("AUTHORIZES", "SUBJECT", "ACTION")
    assert result.result is SemanticResult.INVALID


def test_r2_occupies_office_to_subject_is_invalid():
    result = RelationSemanticValidator().validate("OCCUPIES", "OFFICE", "SUBJECT")
    assert result.result is SemanticResult.INVALID


def test_r2_delegates_subject_to_authority_is_invalid():
    result = RelationSemanticValidator().validate("DELEGATES", "SUBJECT", "AUTHORITY")
    assert result.result is SemanticResult.INVALID


def test_r2_unknown_relation_is_indeterminate():
    result = RelationSemanticValidator().validate("UNKNOWN_RELATION", "SUBJECT", "ACTION")
    assert result.result is SemanticResult.INDETERMINATE
