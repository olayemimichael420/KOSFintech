import database

from models.service_act import ServiceAct, ServiceActStatus
from models.verification import VerificationDecision
from models.verification_outcome import VerificationOutcome

from repositories.service_act_repository import ServiceActRepository
from repositories.verification_repository import VerificationRepository

from services.service_act_service import ServiceActService
from services.service_act_verification_service import (
    ServiceActVerificationService,
)
from services.verification_decision_service import (
    VerificationDecisionService,
)
from services.verification_service import VerificationService


def _setup(tmp_path, monkeypatch):
    db_path = tmp_path / "service_act_verification_integration.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    users = [
        ("tenant-001", "Provider"),
        ("tenant-001", "Recipient"),
        ("tenant-001", "Verifier One"),
        ("tenant-001", "Verifier Two"),
        ("tenant-001", "Verifier Three"),
    ]

    ids = {}

    for tenant_id, name in users:
        cursor = connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            (tenant_id, name, "member"),
        )
        ids[name] = cursor.lastrowid

    connection.commit()

    service_act_repository = ServiceActRepository(connection)
    verification_repository = VerificationRepository(connection)

    act = service_act_repository.create(
        ServiceAct(
            id=None,
            tenant_id="tenant-001",
            provider_user_id=ids["Provider"],
            recipient_user_id=ids["Recipient"],
            title="Mathematics tutoring",
            description="Provide mathematics tutoring.",
            status=ServiceActStatus.CREATED,
        )
    )

    service_act_service = ServiceActService(
        service_act_repository
    )

    verification_service = VerificationService(
        verification_repository,
        service_act_repository,
    )

    decision_service = VerificationDecisionService(
        verification_repository
    )

    finalization_service = ServiceActVerificationService(
        decision_service,
        service_act_service,
    )

    return {
        "connection": connection,
        "act": act,
        "ids": ids,
        "service_act_service": service_act_service,
        "verification_service": verification_service,
        "decision_service": decision_service,
        "finalization_service": finalization_service,
        "verification_repository": verification_repository,
        "service_act_repository": service_act_repository,
    }


def _submit_to_submitted(setup):
    service = setup["service_act_service"]
    act = setup["act"]

    act = service.transition(
        "tenant-001",
        act.id,
        ServiceActStatus.ACCEPTED,
    )

    act = service.transition(
        "tenant-001",
        act.id,
        ServiceActStatus.IN_PROGRESS,
    )

    act = service.transition(
        "tenant-001",
        act.id,
        ServiceActStatus.SUBMITTED,
    )

    return act


def test_two_approvals_complete_real_service_act(
    tmp_path,
    monkeypatch,
):
    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        verification_service = setup["verification_service"]
        finalization_service = setup["finalization_service"]

        ids = setup["ids"]

        first = verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        assert first.decision == VerificationDecision.APPROVED

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.PENDING
        )

        second = verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.APPROVED,
        )

        assert second.decision == VerificationDecision.APPROVED

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.APPROVED
        )

        completed = finalization_service.finalize(
            "tenant-001",
            act.id,
            actor_id=ids["Verifier Two"],
        )

        assert completed.status == ServiceActStatus.COMPLETED
        assert completed.completed_at is not None

        persisted = setup["service_act_repository"].get(
            "tenant-001",
            act.id,
        )

        assert persisted.status == ServiceActStatus.COMPLETED
        assert persisted.completed_at is not None

    finally:
        setup["connection"].close()


def test_two_rejections_cancel_real_service_act(
    tmp_path,
    monkeypatch,
):
    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        verification_service = setup["verification_service"]
        finalization_service = setup["finalization_service"]

        ids = setup["ids"]

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.REJECTED,
            reason="The service was not completed.",
        )

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.PENDING
        )

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.REJECTED,
            reason="The service was not completed.",
        )

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.REJECTED
        )

        cancelled = finalization_service.finalize(
            "tenant-001",
            act.id,
            actor_id=ids["Verifier Two"],
        )

        assert cancelled.status == ServiceActStatus.CANCELLED
        assert cancelled.cancelled_at is not None
        assert (
            cancelled.cancellation_reason
            == "Service Act rejected by verification."
        )

        persisted = setup["service_act_repository"].get(
            "tenant-001",
            act.id,
        )

        assert persisted.status == ServiceActStatus.CANCELLED
        assert persisted.cancelled_at is not None
        assert (
            persisted.cancellation_reason
            == "Service Act rejected by verification."
        )

    finally:
        setup["connection"].close()


def test_one_approval_and_one_rejection_remains_pending(
    tmp_path,
    monkeypatch,
):
    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        verification_service = setup["verification_service"]
        finalization_service = setup["finalization_service"]

        ids = setup["ids"]

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.REJECTED,
            reason="Insufficient completion evidence.",
        )

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.PENDING
        )

        current = finalization_service.finalize(
            "tenant-001",
            act.id,
        )

        assert current.status == ServiceActStatus.SUBMITTED
        assert current.completed_at is None
        assert current.cancelled_at is None

    finally:
        setup["connection"].close()


def test_third_verifier_can_resolve_two_to_one_vote(
    tmp_path,
    monkeypatch,
):
    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        verification_service = setup["verification_service"]
        finalization_service = setup["finalization_service"]

        ids = setup["ids"]

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.REJECTED,
            reason="Evidence was initially insufficient.",
        )

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.PENDING
        )

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Three"],
            VerificationDecision.APPROVED,
        )

        assert (
            setup["decision_service"].evaluate(
                "tenant-001",
                act.id,
            )
            == VerificationOutcome.APPROVED
        )

        completed = finalization_service.finalize(
            "tenant-001",
            act.id,
            actor_id=ids["Verifier Three"],
        )

        assert completed.status == ServiceActStatus.COMPLETED
        assert completed.completed_at is not None

    finally:
        setup["connection"].close()


def test_submitted_act_cannot_be_completed_twice(
    tmp_path,
    monkeypatch,
):
    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        verification_service = setup["verification_service"]
        finalization_service = setup["finalization_service"]

        ids = setup["ids"]

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        verification_service.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.APPROVED,
        )

        completed = finalization_service.finalize(
            "tenant-001",
            act.id,
            actor_id=ids["Verifier Two"],
        )

        assert completed.status == ServiceActStatus.COMPLETED

        try:
            finalization_service.finalize(
                "tenant-001",
                act.id,
                actor_id=ids["Verifier Two"],
            )
        except ValueError as exc:
            assert "invalid service act transition" in str(exc)
        else:
            raise AssertionError(
                "Completed Service Act was finalized twice"
            )

    finally:
        setup["connection"].close()


def test_workflow_two_approvals_auto_completes_service_act(
    tmp_path,
    monkeypatch,
):
    from services.verification_workflow_service import (
        VerificationWorkflowService,
    )

    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        workflow = VerificationWorkflowService(
            setup["verification_service"],
            setup["finalization_service"],
        )

        ids = setup["ids"]

        first_verification, first_act = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        assert first_verification.decision == (
            VerificationDecision.APPROVED
        )
        assert first_act.status == ServiceActStatus.SUBMITTED

        second_verification, completed = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.APPROVED,
        )

        assert second_verification.decision == (
            VerificationDecision.APPROVED
        )
        assert completed.status == ServiceActStatus.COMPLETED
        assert completed.completed_at is not None

        persisted = setup["service_act_repository"].get(
            "tenant-001",
            act.id,
        )

        assert persisted.status == ServiceActStatus.COMPLETED
        assert persisted.completed_at is not None

    finally:
        setup["connection"].close()


def test_workflow_two_rejections_auto_cancels_service_act(
    tmp_path,
    monkeypatch,
):
    from services.verification_workflow_service import (
        VerificationWorkflowService,
    )

    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        workflow = VerificationWorkflowService(
            setup["verification_service"],
            setup["finalization_service"],
        )

        ids = setup["ids"]

        _, first_act = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.REJECTED,
            reason="Service evidence was insufficient.",
        )

        assert first_act.status == ServiceActStatus.SUBMITTED

        _, cancelled = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.REJECTED,
            reason="Service evidence was insufficient.",
        )

        assert cancelled.status == ServiceActStatus.CANCELLED
        assert cancelled.cancelled_at is not None
        assert (
            cancelled.cancellation_reason
            == "Service Act rejected by verification."
        )

        persisted = setup["service_act_repository"].get(
            "tenant-001",
            act.id,
        )

        assert persisted.status == ServiceActStatus.CANCELLED

    finally:
        setup["connection"].close()


def test_workflow_split_vote_waits_for_third_verifier(
    tmp_path,
    monkeypatch,
):
    from services.verification_workflow_service import (
        VerificationWorkflowService,
    )

    setup = _setup(tmp_path, monkeypatch)

    try:
        act = _submit_to_submitted(setup)

        workflow = VerificationWorkflowService(
            setup["verification_service"],
            setup["finalization_service"],
        )

        ids = setup["ids"]

        _, first_act = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier One"],
            VerificationDecision.APPROVED,
        )

        assert first_act.status == ServiceActStatus.SUBMITTED

        _, second_act = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier Two"],
            VerificationDecision.REJECTED,
            reason="Insufficient evidence.",
        )

        assert second_act.status == ServiceActStatus.SUBMITTED

        _, completed = workflow.verify(
            "tenant-001",
            act.id,
            ids["Verifier Three"],
            VerificationDecision.APPROVED,
        )

        assert completed.status == ServiceActStatus.COMPLETED
        assert completed.completed_at is not None

    finally:
        setup["connection"].close()
