from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

QUEST = ROOT / "docs/SMOS_GOVERNANCE_QUEST_CONSTITUTIONAL_DEPENDENCY_MATRIX.md"
PROTOCOL = ROOT / "docs/SMOS_GOVERNANCE_QUEST_DECISION_GATE_PROTOCOL.md"
SEMANTICS = ROOT / "docs/SMOS_GOVERNANCE_QUEST_DECISION_STATE_SEMANTICS.md"


def read(path):
    assert path.exists(), f"Required governance document missing: {path}"
    return path.read_text()


def test_governance_documents_exist():
    for path in (QUEST, PROTOCOL, SEMANTICS):
        assert path.exists()


def test_protocol_defines_exactly_four_decision_states():
    text = read(PROTOCOL)

    for state in ("ACCEPT", "DECLINE", "REJECT", "PENDING"):
        assert f"### {state}" in text

    assert "Every consequential question shall resolve to one of four permitted decision states." in text


def test_semantics_defines_the_same_four_states():
    text = read(SEMANTICS)

    for state in ("ACCEPT", "DECLINE", "REJECT", "PENDING"):
        assert state in text

    assert "GATE ≠ DECISION STATE" in text


def test_five_gate_model_is_preserved():
    text = read(QUEST)

    required = (
        "Gate 1 — Eligibility",
        "Gate 2 — Qualification",
        "Gate 3 — Authority",
        "Gate 4 — Mandate",
        "Gate 5 — Execution",
    )

    for gate in required:
        assert gate in text


def test_quest_does_not_create_authority():
    text = read(QUEST)

    assert "The Quest MUST NOT independently:" in text
    assert "EXECUTABLE AUTHORIZATION = NOT GRANTED" in text

    forbidden_creation_claims = (
        "the Quest creates constitutional authority",
        "the Quest creates amendment authority",
        "the Quest creates jurisdiction",
        "the Quest creates executable authorization",
    )

    for claim in forbidden_creation_claims:
        assert claim not in text.lower()


def test_protocol_does_not_equate_accept_with_authorization():
    text = read(PROTOCOL)

    assert "ACCEPT does not independently grant executable authorization." in text
    assert "An accepted proposition does not automatically constitute executable authorization." in text


def test_semantics_does_not_equate_accept_with_authorization():
    text = read(SEMANTICS)

    assert "authorization has automatically been granted;" in text
    assert "ACCEPT" in text
    assert "EXECUTABLE AUTHORIZATION" in text


def test_pending_is_fail_closed():
    protocol = read(PROTOCOL)
    semantics = read(SEMANTICS)

    assert "PENDING is a hard non-proceed state." in protocol
    assert "PENDING shall never be treated as implicit ACCEPT." in protocol
    assert "PENDING = NO PROCEED" in semantics
    assert "EXECUTION = BLOCKED" in semantics


def test_dependency_propagation_is_fail_closed():
    protocol = read(PROTOCOL)
    semantics = read(SEMANTICS)

    assert "A mandatory PENDING or UNSATISFIED dependency blocks downstream execution." in protocol
    assert "A downstream question cannot become executable merely because its own decision appears favorable." in protocol
    assert "An upstream ACCEPT does not automatically produce downstream ACCEPT." in semantics


def test_execution_requires_separate_conditions():
    protocol = read(PROTOCOL)
    semantics = read(SEMANTICS)

    assert "REQUIRED_AUTHORITY_ESTABLISHED" in protocol
    assert "MANDATORY_DEPENDENCIES_SATISFIED" in protocol
    assert "REQUIRED_AUTHORIZATION_ESTABLISHED" in protocol
    assert "SCOPE_VALID" in protocol

    assert "EXECUTION = BLOCKED" in semantics


def test_semantic_layer_does_not_create_constitutional_authority():
    text = read(SEMANTICS)

    assert "creates constitutional authority;" in text
    assert "creates executable authorization;" in text
    assert "A semantic classification is not itself a source of authority." in text
