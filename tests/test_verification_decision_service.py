from types import SimpleNamespace

import pytest

from models.verification import VerificationDecision
from models.verification_outcome import VerificationOutcome
from services.verification_decision_service import VerificationDecisionService


class FakeVerificationRepository:
    def __init__(self, verifications):
        self.verifications = verifications

    def list_by_act(self, tenant_id, service_act_id):
        return [
            verification
            for verification in self.verifications
            if verification.tenant_id == tenant_id
            and verification.service_act_id == service_act_id
        ]


def verification(tenant_id, act_id, user_id, decision):
    return SimpleNamespace(
        tenant_id=tenant_id,
        service_act_id=act_id,
        verifier_user_id=user_id,
        decision=decision,
    )


def test_two_approvals_produce_approved():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 11, VerificationDecision.APPROVED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.APPROVED


def test_two_rejections_produce_rejected():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.REJECTED),
        verification("tenant-001", 1, 11, VerificationDecision.REJECTED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.REJECTED


def test_one_approval_is_pending():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.APPROVED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.PENDING


def test_one_rejection_is_pending():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.REJECTED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.PENDING


def test_mixed_three_votes_with_two_approvals_is_approved():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 11, VerificationDecision.REJECTED),
        verification("tenant-001", 1, 12, VerificationDecision.APPROVED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.APPROVED


def test_mixed_three_votes_with_two_rejections_is_rejected():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.REJECTED),
        verification("tenant-001", 1, 11, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 12, VerificationDecision.REJECTED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.REJECTED


def test_other_tenants_are_ignored():
    repository = FakeVerificationRepository([
        verification("tenant-002", 1, 10, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 11, VerificationDecision.APPROVED),
    ])

    service = VerificationDecisionService(repository)

    assert service.evaluate("tenant-001", 1) == VerificationOutcome.PENDING


def test_more_than_three_verifications_is_rejected():
    repository = FakeVerificationRepository([
        verification("tenant-001", 1, 10, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 11, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 12, VerificationDecision.APPROVED),
        verification("tenant-001", 1, 13, VerificationDecision.APPROVED),
    ])

    service = VerificationDecisionService(repository)

    with pytest.raises(ValueError, match="maximum allowed"):
        service.evaluate("tenant-001", 1)
