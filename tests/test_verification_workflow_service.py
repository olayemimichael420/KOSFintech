from types import SimpleNamespace

import pytest

from models.service_act import ServiceActStatus
from models.verification import VerificationDecision
from services.verification_workflow_service import (
    VerificationWorkflowService,
)


class FakeVerificationService:
    def __init__(self):
        self.calls = []

    def verify(
        self,
        tenant_id,
        service_act_id,
        verifier_user_id,
        decision,
        reason=None,
    ):
        self.calls.append(
            (
                tenant_id,
                service_act_id,
                verifier_user_id,
                decision,
                reason,
            )
        )

        return SimpleNamespace(
            id=100,
            tenant_id=tenant_id,
            service_act_id=service_act_id,
            verifier_user_id=verifier_user_id,
            decision=decision,
            reason=reason,
        )


class FakeServiceActVerificationService:
    def __init__(self, service_act):
        self.service_act = service_act
        self.calls = []

    def finalize(
        self,
        tenant_id,
        service_act_id,
        actor_id=None,
    ):
        self.calls.append(
            (
                tenant_id,
                service_act_id,
                actor_id,
            )
        )

        return self.service_act


def test_workflow_records_verification_and_finalizes():
    verification_service = FakeVerificationService()

    service_act = SimpleNamespace(
        id=7,
        status=ServiceActStatus.COMPLETED,
    )

    finalization_service = FakeServiceActVerificationService(
        service_act
    )

    workflow = VerificationWorkflowService(
        verification_service,
        finalization_service,
    )

    verification, updated_act = workflow.verify(
        tenant_id="tenant-001",
        service_act_id=7,
        verifier_user_id=11,
        decision=VerificationDecision.APPROVED,
    )

    assert verification.id == 100
    assert updated_act.status == ServiceActStatus.COMPLETED

    assert verification_service.calls == [
        (
            "tenant-001",
            7,
            11,
            VerificationDecision.APPROVED,
            None,
        )
    ]

    assert finalization_service.calls == [
        (
            "tenant-001",
            7,
            11,
        )
    ]


def test_workflow_passes_rejection_reason():
    verification_service = FakeVerificationService()

    service_act = SimpleNamespace(
        id=7,
        status=ServiceActStatus.SUBMITTED,
    )

    finalization_service = FakeServiceActVerificationService(
        service_act
    )

    workflow = VerificationWorkflowService(
        verification_service,
        finalization_service,
    )

    verification, updated_act = workflow.verify(
        tenant_id="tenant-001",
        service_act_id=7,
        verifier_user_id=12,
        decision=VerificationDecision.REJECTED,
        reason="Insufficient evidence.",
    )

    assert verification.reason == "Insufficient evidence."
    assert updated_act.status == ServiceActStatus.SUBMITTED

    assert verification_service.calls[0][-1] == (
        "Insufficient evidence."
    )


def test_workflow_uses_explicit_actor_id():
    verification_service = FakeVerificationService()

    service_act = SimpleNamespace(
        id=7,
        status=ServiceActStatus.COMPLETED,
    )

    finalization_service = FakeServiceActVerificationService(
        service_act
    )

    workflow = VerificationWorkflowService(
        verification_service,
        finalization_service,
    )

    workflow.verify(
        tenant_id="tenant-001",
        service_act_id=7,
        verifier_user_id=11,
        decision=VerificationDecision.APPROVED,
        actor_id=99,
    )

    assert finalization_service.calls == [
        (
            "tenant-001",
            7,
            99,
        )
    ]


def test_verification_failure_prevents_finalization():
    class FailingVerificationService:
        def verify(self, **kwargs):
            raise ValueError("verification failed")

    finalization_service = FakeServiceActVerificationService(
        SimpleNamespace(
            id=7,
            status=ServiceActStatus.SUBMITTED,
        )
    )

    workflow = VerificationWorkflowService(
        FailingVerificationService(),
        finalization_service,
    )

    with pytest.raises(ValueError, match="verification failed"):
        workflow.verify(
            tenant_id="tenant-001",
            service_act_id=7,
            verifier_user_id=11,
            decision=VerificationDecision.APPROVED,
        )

    assert finalization_service.calls == []


def test_pending_result_is_returned_without_forcing_completion():
    verification_service = FakeVerificationService()

    service_act = SimpleNamespace(
        id=7,
        status=ServiceActStatus.SUBMITTED,
    )

    finalization_service = FakeServiceActVerificationService(
        service_act
    )

    workflow = VerificationWorkflowService(
        verification_service,
        finalization_service,
    )

    verification, updated_act = workflow.verify(
        tenant_id="tenant-001",
        service_act_id=7,
        verifier_user_id=11,
        decision=VerificationDecision.APPROVED,
    )

    assert verification.decision == VerificationDecision.APPROVED
    assert updated_act.status == ServiceActStatus.SUBMITTED
