from models.verification import Verification, VerificationDecision


def test_verification_model_defaults():
    verification = Verification(
        id=None,
        tenant_id="tenant-001",
        service_act_id=1,
        verifier_user_id=2,
        decision=VerificationDecision.APPROVED,
    )

    assert verification.id is None
    assert verification.tenant_id == "tenant-001"
    assert verification.service_act_id == 1
    assert verification.verifier_user_id == 2
    assert verification.decision == VerificationDecision.APPROVED
    assert verification.reason is None


def test_verification_rejection_can_have_reason():
    verification = Verification(
        id=None,
        tenant_id="tenant-001",
        service_act_id=1,
        verifier_user_id=3,
        decision=VerificationDecision.REJECTED,
        reason="Service was not completed as described",
    )

    assert verification.decision == VerificationDecision.REJECTED
    assert verification.reason == "Service was not completed as described"
