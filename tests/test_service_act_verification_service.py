from types import SimpleNamespace

from models.service_act import ServiceActStatus
from models.verification_outcome import VerificationOutcome
from services.service_act_verification_service import (
    ServiceActVerificationService,
)


class FakeDecisionService:
    def __init__(self, outcome):
        self.outcome = outcome

    def evaluate(self, tenant_id, service_act_id):
        return self.outcome


class FakeServiceActService:
    def __init__(self):
        self.calls = []
        self.repository = SimpleNamespace(
            connection=TransactionConnection()
        )

    def transition(
        self,
        tenant_id,
        service_act_id,
        target_status,
        cancellation_reason=None,
        commit=True,
        actor_id=None,
    ):
        self.calls.append(
            (
                tenant_id,
                service_act_id,
                target_status,
                cancellation_reason,
            )
        )
        return "updated"


def test_approved_outcome_completes_service_act():
    decision = FakeDecisionService(VerificationOutcome.APPROVED)
    service_act = FakeServiceActService()

    service = ServiceActVerificationService(decision, service_act)

    assert service.finalize("tenant-001", 7) == "updated"
    assert service_act.calls == [
        (
            "tenant-001",
            7,
            ServiceActStatus.COMPLETED,
            None,
        )
    ]


def test_rejected_outcome_cancels_service_act():
    decision = FakeDecisionService(VerificationOutcome.REJECTED)
    service_act = FakeServiceActService()

    service = ServiceActVerificationService(decision, service_act)

    assert service.finalize("tenant-001", 7) == "updated"
    assert service_act.calls == [
        (
            "tenant-001",
            7,
            ServiceActStatus.CANCELLED,
            "Service Act rejected by verification.",
        )
    ]


def test_pending_outcome_does_not_transition():
    decision = FakeDecisionService(VerificationOutcome.PENDING)
    service_act = FakeServiceActService()

    service_act.repository.get = lambda tenant_id, service_act_id: "unchanged"

    service = ServiceActVerificationService(decision, service_act)

    assert service.finalize("tenant-001", 7) == "unchanged"
    assert service_act.calls == []


def test_approved_finalization_emits_audit_event(caplog):
    import json
    import logging

    decision = FakeDecisionService(
        VerificationOutcome.APPROVED
    )
    service_act = FakeServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    with caplog.at_level(
        logging.INFO,
        logger="kosfintech.audit",
    ):
        result = service.finalize(
            "tenant-001",
            7,
            actor_id=11,
        )

    assert result == "updated"

    records = [
        record
        for record in caplog.records
        if record.name == "kosfintech.audit"
    ]

    assert len(records) == 1

    payload = json.loads(
        records[0].message[len("AUDIT "):]
    )

    assert payload["event_type"] == (
        "service_act_completed_by_verification"
    )
    assert payload["actor_id"] == 11
    assert payload["tenant_id"] == "tenant-001"
    assert payload["action"] == (
        "complete_service_act_by_verification"
    )
    assert payload["metadata"]["service_act_id"] == 7
    assert payload["metadata"]["verification_outcome"] == "approved"


def test_rejected_finalization_emits_audit_event(caplog):
    import json
    import logging

    decision = FakeDecisionService(
        VerificationOutcome.REJECTED
    )
    service_act = FakeServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    with caplog.at_level(
        logging.INFO,
        logger="kosfintech.audit",
    ):
        result = service.finalize(
            "tenant-001",
            7,
            actor_id=12,
        )

    assert result == "updated"

    records = [
        record
        for record in caplog.records
        if record.name == "kosfintech.audit"
    ]

    assert len(records) == 1

    payload = json.loads(
        records[0].message[len("AUDIT "):]
    )

    assert payload["event_type"] == (
        "service_act_cancelled_by_verification"
    )
    assert payload["actor_id"] == 12
    assert payload["tenant_id"] == "tenant-001"
    assert payload["action"] == (
        "cancel_service_act_by_verification"
    )
    assert payload["metadata"]["service_act_id"] == 7
    assert payload["metadata"]["verification_outcome"] == "rejected"


class TransactionConnection:
    def __init__(self):
        self.events = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, parameters=None):
        self.events.append(
            (statement, parameters)
        )

        class Cursor:
            lastrowid = 1

            def fetchone(self):
                return None

        return Cursor()

    def commit(self):
        self.commits += 1
        self.events.append("COMMIT")

    def rollback(self):
        self.rollbacks += 1
        self.events.append("ROLLBACK")


class TransactionRepository:
    def __init__(self):
        self.connection = TransactionConnection()
        self.status = ServiceActStatus.SUBMITTED

    def get(self, tenant_id, service_act_id):
        return self.status


class TransactionServiceActService:
    def __init__(self):
        self.repository = TransactionRepository()
        self.calls = []

    def transition(
        self,
        tenant_id,
        service_act_id,
        target_status,
        cancellation_reason=None,
        commit=True,
        actor_id=None,
    ):
        self.calls.append(
            (
                tenant_id,
                service_act_id,
                target_status,
                cancellation_reason,
                commit,
            )
        )
        self.repository.status = target_status
        return "updated"


def test_approved_finalization_uses_single_transaction(monkeypatch):
    decision = FakeDecisionService(VerificationOutcome.APPROVED)
    service_act = TransactionServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    service.finalize(
        "tenant-001",
        7,
        actor_id=11,
    )

    assert service_act.repository.connection.commits == 1
    assert service_act.repository.connection.rollbacks == 0

    assert service_act.calls == [
        (
            "tenant-001",
            7,
            ServiceActStatus.COMPLETED,
            None,
            False,
        )
    ]


def test_rejected_finalization_uses_single_transaction(monkeypatch):
    decision = FakeDecisionService(VerificationOutcome.REJECTED)
    service_act = TransactionServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    service.finalize(
        "tenant-001",
        7,
        actor_id=12,
    )

    assert service_act.repository.connection.commits == 1
    assert service_act.repository.connection.rollbacks == 0

    assert service_act.calls == [
        (
            "tenant-001",
            7,
            ServiceActStatus.CANCELLED,
            "Service Act rejected by verification.",
            False,
        )
    ]


def test_approved_finalization_rolls_back_when_audit_fails(monkeypatch):
    decision = FakeDecisionService(VerificationOutcome.APPROVED)
    service_act = TransactionServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    def failing_audit_event(*args, **kwargs):
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(
        "services.service_act_verification_service.audit_event",
        failing_audit_event,
    )

    try:
        service.finalize(
            "tenant-001",
            7,
            actor_id=11,
        )
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "simulated audit failure"

    assert service_act.repository.connection.commits == 0
    assert service_act.repository.connection.rollbacks == 1


def test_rejected_finalization_rolls_back_when_audit_fails(monkeypatch):
    decision = FakeDecisionService(VerificationOutcome.REJECTED)
    service_act = TransactionServiceActService()

    service = ServiceActVerificationService(
        decision,
        service_act,
    )

    def failing_audit_event(*args, **kwargs):
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(
        "services.service_act_verification_service.audit_event",
        failing_audit_event,
    )

    try:
        service.finalize(
            "tenant-001",
            7,
            actor_id=12,
        )
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "simulated audit failure"

    assert service_act.repository.connection.commits == 0
    assert service_act.repository.connection.rollbacks == 1
