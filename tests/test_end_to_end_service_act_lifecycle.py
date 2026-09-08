import database
import pytest

from models.service_act import ServiceActStatus
from models.service_request import ServiceRequest, ServiceRequestStatus
from models.verification import VerificationDecision
from models.dispute import (
    DisputeResolution,
    DisputeStatus,
)

from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


@pytest.fixture
def connection(tmp_path, monkeypatch):
    db_path = tmp_path / "e2e_lifecycle.db"
    monkeypatch.setenv("DB_FILE", str(db_path))

    database.init_db()
    connection = database.get_connection()

    try:
        yield connection
    finally:
        connection.close()


def _create_users(
    connection,
    tenant_id,
    provider_id,
    recipient_id,
    verifier_1,
    verifier_2,
    dispute_reviewer,
):
    users = [
        ("Provider", "provider"),
        ("Recipient", "recipient"),
        ("Verifier One", "member"),
        ("Verifier Two", "member"),
        ("Dispute Reviewer", "admin1"),
    ]

    user_ids = []

    for name, role in users:
        email = name.lower().replace(" ", ".") + "@e2e.test"

        cursor = connection.execute(
            """
            INSERT INTO users (
                tenant_id,
                name,
                email,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                name,
                email,
                role,
                "active",
            ),
        )

        user_ids.append(cursor.lastrowid)

    # Grant the Service Act lifecycle permission to the provider and recipient.
    # The ServiceActService authorization boundary requires an active
    # tenant-scoped application permission for externally initiated transitions.
    permission_cursor = connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, 'service_act.write', 'active')
        """,
        (tenant_id,),
    )
    permission_id = permission_cursor.lastrowid

    for user_id, role_name in (
        (user_ids[0], "e2e-service-act-provider"),
        (user_ids[1], "e2e-service-act-recipient"),
    ):
        role_cursor = connection.execute(
            """
            INSERT INTO roles (tenant_id, name, status)
            VALUES (?, ?, 'active')
            """,
            (tenant_id, role_name),
        )
        role_id = role_cursor.lastrowid

        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            """,
            (tenant_id, user_id, role_id),
        )

        connection.execute(
            """
            INSERT INTO role_permissions (tenant_id, role_id, permission_id)
            VALUES (?, ?, ?)
            """,
            (tenant_id, role_id, permission_id),
        )

    # Grant verification.write only to the two independent E2E verifiers.
    permission_cursor = connection.execute(
        '''
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, 'verification.write', 'active')
        ''',
        (tenant_id,),
    )
    permission_id = permission_cursor.lastrowid

    for user_id, role_name in (
        (user_ids[2], "e2e-verification-verifier-1"),
        (user_ids[3], "e2e-verification-verifier-2"),
    ):
        role_cursor = connection.execute(
            '''
            INSERT INTO roles (tenant_id, name, status)
            VALUES (?, ?, 'active')
            ''',
            (tenant_id, role_name),
        )
        role_id = role_cursor.lastrowid

        connection.execute(
            '''
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            ''',
            (tenant_id, user_id, role_id),
        )

        connection.execute(
            '''
            INSERT INTO role_permissions (
                tenant_id,
                role_id,
                permission_id
            )
            VALUES (?, ?, ?)
            ''',
            (tenant_id, role_id, permission_id),
        )

    # Grant talent_point.issue to the provider for E2E TP issuance.
    permission_cursor = connection.execute(
        '''
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, 'talent_point.issue', 'active')
        ''',
        (tenant_id,),
    )
    permission_id = permission_cursor.lastrowid

    role_cursor = connection.execute(
        '''
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, 'e2e-talent-point-issuer', 'active')
        ''',
        (tenant_id,),
    )
    role_id = role_cursor.lastrowid

    connection.execute(
        '''
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        ''',
        (tenant_id, user_ids[0], role_id),
    )

    connection.execute(
        '''
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        ''',
        (tenant_id, role_id, permission_id),
    )

    # Grant service_request.write only to the provider/requester.
    permission_cursor = connection.execute(
        '''
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, 'service_request.write', 'active')
        ''',
        (tenant_id,),
    )
    permission_id = permission_cursor.lastrowid

    role_cursor = connection.execute(
        '''
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, 'e2e-service-request-requester', 'active')
        ''',
        (tenant_id,),
    )
    role_id = role_cursor.lastrowid

    connection.execute(
        '''
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        ''',
        (tenant_id, user_ids[0], role_id),
    )

    connection.execute(
        '''
        INSERT INTO role_permissions (tenant_id, role_id, permission_id)
        VALUES (?, ?, ?)
        ''',
        (tenant_id, role_id, permission_id),
    )

    connection.commit()
    return tuple(user_ids)


def _create_service_act(services, tenant_id, provider_id, recipient_id):
    request = services.service_request.create(
        ServiceRequest(
            id=None,
            tenant_id=tenant_id,
            requester_user_id=provider_id,
            recipient_user_id=recipient_id,
            title="E2E Test Service",
            description="End-to-end lifecycle integration test",
        ),
        actor_id=provider_id,
    )

    request = services.service_request.transition(
        tenant_id,
        request.id,
        ServiceRequestStatus.AUTHORIZED,
        actor_id=provider_id,
    )

    act = services.service_act.create(
        request,
        provider_user_id=provider_id,
        actor_id=provider_id,
    )

    return request, act


def test_complete_service_act_lifecycle(connection):
    tenant_id = "e2e-tenant"
    provider_id = 1001
    recipient_id = 1002
    verifier_1 = 1003
    verifier_2 = 1004
    dispute_reviewer = 1999

    services = ApplicationServices(
        ApplicationServiceFactory(connection)
    )

    # ---------------------------------------------------------
    # 1. CREATE E2E USERS
    # ---------------------------------------------------------
    (
        provider_id,
        recipient_id,
        verifier_1,
        verifier_2,
        dispute_reviewer,
    ) = _create_users(
        connection,
        tenant_id,
        provider_id,
        recipient_id,
        verifier_1,
        verifier_2,
        dispute_reviewer,
    )

    # Use the actual database-generated recipient identity.
    dispute_actor = recipient_id

    # ---------------------------------------------------------
    # 2. AUTHORIZE SERVICE REQUEST + CREATE SERVICE ACT
    # ---------------------------------------------------------
    service_request, act = _create_service_act(
        services,
        tenant_id,
        provider_id,
        recipient_id,
    )

    assert service_request.status == ServiceRequestStatus.AUTHORIZED

    service_act_id = act.id

    assert act is not None
    assert act.status == ServiceActStatus.CREATED

    # ---------------------------------------------------------
    # 2. ACCEPT
    # ---------------------------------------------------------
    act = services.service_act.transition(
        tenant_id,
        service_act_id,
        ServiceActStatus.ACCEPTED,
        actor_id=recipient_id,
    )

    assert act.status == ServiceActStatus.ACCEPTED

    # ---------------------------------------------------------
    # 3. START
    # ---------------------------------------------------------
    act = services.service_act.transition(
        tenant_id,
        service_act_id,
        ServiceActStatus.IN_PROGRESS,
        actor_id=provider_id,
    )

    assert act.status == ServiceActStatus.IN_PROGRESS

    # ---------------------------------------------------------
    # 4. SUBMIT
    # ---------------------------------------------------------
    act = services.service_act.transition(
        tenant_id,
        service_act_id,
        ServiceActStatus.SUBMITTED,
        actor_id=provider_id,
    )

    assert act.status == ServiceActStatus.SUBMITTED

    # ---------------------------------------------------------
    # 5. INDEPENDENT VERIFICATION #1
    # ---------------------------------------------------------
    verification_1 = services.verification.verify(
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        verifier_user_id=verifier_1,
        decision=VerificationDecision.APPROVED,
        actor_user_id=verifier_1,
    )

    assert verification_1.decision == VerificationDecision.APPROVED

    # ---------------------------------------------------------
    # 6. INDEPENDENT VERIFICATION #2
    # ---------------------------------------------------------
    verification_2 = services.verification.verify(
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        verifier_user_id=verifier_2,
        decision=VerificationDecision.APPROVED,
        actor_user_id=verifier_2,
    )

    assert verification_2.decision == VerificationDecision.APPROVED

    # ---------------------------------------------------------
    # 7. FINALIZE AGGREGATE VERIFICATION
    # ---------------------------------------------------------
    act = services.verification_workflow.service_act_verification_service.finalize(
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        actor_id=verifier_1,
    )

    assert act.status == ServiceActStatus.COMPLETED

    # ---------------------------------------------------------
    # 8. ISSUE TALENT POINTS
    # ---------------------------------------------------------
    transaction = services.talent_point_issuance.issue_for_service_act(
        tenant_id=tenant_id,
        service_act=act,
        amount=100,
        reference="E2E-TEST",
        actor_user_id=provider_id,
    )

    assert transaction.amount == 100
    assert transaction.user_id == provider_id
    assert transaction.service_act_id == service_act_id

    # ---------------------------------------------------------
    # 9. SUBMIT REPUTATION
    # ---------------------------------------------------------
    reputation = services.reputation.submit(
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        reviewer_user_id=recipient_id,
        score=5,
        comment="Excellent service.",
    )

    assert reputation.score == 5
    assert reputation.subject_user_id == provider_id
    assert reputation.reviewer_user_id == recipient_id

    # ---------------------------------------------------------
    # 10. OPEN DISPUTE
    # ---------------------------------------------------------
    dispute = services.dispute.open_dispute(
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        initiator_user_id=dispute_actor,
        reason="Post-completion lifecycle test dispute.",
    )

    assert dispute.status == DisputeStatus.OPEN
    assert dispute.service_act_id == service_act_id

    # ---------------------------------------------------------
    # 11. MOVE DISPUTE TO REVIEW
    # ---------------------------------------------------------
    dispute = services.dispute.move_to_review(
        tenant_id=tenant_id,
        dispute_id=dispute.id,
        actor_user_id=dispute_reviewer,
    )

    assert dispute.status == DisputeStatus.UNDER_REVIEW

    # ---------------------------------------------------------
    # 12. RESOLVE DISPUTE
    # ---------------------------------------------------------
    dispute = services.dispute.resolve(
        tenant_id=tenant_id,
        dispute_id=dispute.id,
        resolved_by_user_id=dispute_reviewer,
        resolution=DisputeResolution.RECIPIENT_FAVORED,
        resolution_reason="E2E lifecycle resolution.",
    )

    assert dispute.status == DisputeStatus.RESOLVED
    assert dispute.resolution == DisputeResolution.RECIPIENT_FAVORED

    # ---------------------------------------------------------
    # 13. FINAL SERVICE ACT STATE
    # ---------------------------------------------------------
    final_act = services.service_act.repository.get(
        tenant_id,
        service_act_id,
    )

    assert final_act.status == ServiceActStatus.COMPLETED

    # ---------------------------------------------------------
    # 14. VERIFY TALENT POINT ISSUANCE PERSISTED
    # ---------------------------------------------------------
    assert (
        services.talent_point_issuance.repository
        .issuance_exists_for_service_act(
            tenant_id,
            service_act_id,
        )
    )

    # ---------------------------------------------------------
    # 15. VERIFY REPUTATION PERSISTED
    # ---------------------------------------------------------
    assert (
        services.reputation.repository
        .exists_for_service_act(
            tenant_id,
            service_act_id,
        )
    )

    # ---------------------------------------------------------
    # 16. VERIFY DISPUTE FINAL STATE
    # ---------------------------------------------------------
    persisted_dispute = services.dispute.repository.get(
        tenant_id,
        dispute.id,
    )

    assert persisted_dispute.status == DisputeStatus.RESOLVED


    # ---------------------------------------------------------
    # 17. VERIFY AUDIT EVENTS PERSISTED
    # ---------------------------------------------------------
    audit_rows = connection.execute(
        """
        SELECT event_type, actor_id, tenant_id, action, metadata
        FROM audit_events
        WHERE tenant_id = ?
          AND (
              metadata LIKE ?
              OR metadata LIKE ?
          )
        ORDER BY id
        """,
        (
            tenant_id,
            f'%"service_act_id": {service_act_id}%',
            f'%"service_act_id": {service_act_id}%'.replace(
                f'%"service_act_id": {service_act_id}%',
                f'%\\"service_act_id\\": {service_act_id}%'
            ),
        ),
    ).fetchall()

    assert len(audit_rows) == 9

    audit_event_types = [row["event_type"] for row in audit_rows]

    assert "service_act_created" in audit_event_types
    assert audit_event_types.count("verification_submitted") == 2
    assert "service_act_completed_by_verification" in audit_event_types
    assert "talent_point_issuance" in audit_event_types
    assert "reputation_submitted" in audit_event_types
    assert "dispute_opened" in audit_event_types
    assert "dispute_under_review" in audit_event_types
    assert "dispute_resolved" in audit_event_types

    # Verify every lifecycle audit event is tenant-scoped.
    assert all(row["tenant_id"] == tenant_id for row in audit_rows)

    # Verify the principal audit actors.
    assert any(
        row["event_type"] == "service_act_created"
        and row["actor_id"] == provider_id
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "verification_submitted"
        and row["actor_id"] == verifier_1
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "verification_submitted"
        and row["actor_id"] == verifier_2
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "service_act_completed_by_verification"
        and row["actor_id"] == verifier_1
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "talent_point_issuance"
        and row["actor_id"] == provider_id
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "reputation_submitted"
        and row["actor_id"] == recipient_id
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "dispute_opened"
        and row["actor_id"] == recipient_id
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "dispute_under_review"
        and row["actor_id"] == dispute_reviewer
        for row in audit_rows
    )

    assert any(
        row["event_type"] == "dispute_resolved"
        and row["actor_id"] == dispute_reviewer
        for row in audit_rows
    )
