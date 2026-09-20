from models.learning_evidence import LearningEvidence


def test_learning_evidence_defaults():
    evidence = LearningEvidence(
        id=None,
        tenant_id="tenant-a",
        membership_id=1,
        teaching_content_id=2,
        evidence_date="2026-09-19",
        description="Member demonstrated understanding of the teaching content.",
    )

    assert evidence.id is None
    assert evidence.tenant_id == "tenant-a"
    assert evidence.membership_id == 1
    assert evidence.teaching_content_id == 2
    assert evidence.evidence_date == "2026-09-19"
    assert evidence.description == (
        "Member demonstrated understanding of the teaching content."
    )
    assert evidence.remark is None


def test_learning_evidence_accepts_remark():
    evidence = LearningEvidence(
        id=7,
        tenant_id="tenant-a",
        membership_id=3,
        teaching_content_id=4,
        evidence_date="2026-09-20",
        description="Member submitted a written reflection.",
        remark="Recorded during the teaching session.",
    )

    assert evidence.id == 7
    assert evidence.remark == "Recorded during the teaching session."


def test_learning_evidence_is_immutable():
    evidence = LearningEvidence(
        id=None,
        tenant_id="tenant-a",
        membership_id=1,
        teaching_content_id=2,
        evidence_date="2026-09-19",
        description="Observable evidence.",
    )

    try:
        evidence.description = "Changed"
        assert False, "LearningEvidence should be immutable"
    except AttributeError:
        pass
