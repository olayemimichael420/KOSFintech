from repositories.dispute_repository import DisputeRepository
from models.dispute import (
    Dispute,
    DisputeInitiatorRole,
    DisputeResolution,
    DisputeStatus,
)


def _seed_service_act(db_connection, tenant_id, provider_id, recipient_id):
    cursor = db_connection.execute(
        """
        INSERT INTO service_acts (
            tenant_id,
            provider_user_id,
            recipient_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            provider_id,
            recipient_id,
            "Test Service",
            "Repository test service act",
            "completed",
        ),
    )
    db_connection.commit()
    return cursor.lastrowid


def _seed_users(db_connection, tenant_id):
    users = []

    for name, email in (
        ("Provider", f"provider@{tenant_id}.test"),
        ("Recipient", f"recipient@{tenant_id}.test"),
    ):
        cursor = db_connection.execute(
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
                "member",
                "active",
            ),
        )
        users.append(cursor.lastrowid)

    db_connection.commit()
    return users


def _make_dispute(
    tenant_id,
    service_act_id,
    initiator_user_id,
):
    return Dispute(
        id=None,
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        initiator_user_id=initiator_user_id,
        initiator_role=DisputeInitiatorRole.PROVIDER,
        reason="Service was not delivered as agreed.",
    )


def test_create_and_get_dispute(db_connection):
    tenant_id = "tenant-a"
    provider_id, recipient_id = _seed_users(db_connection, tenant_id)

    service_act_id = _seed_service_act(
        db_connection,
        tenant_id,
        provider_id,
        recipient_id,
    )

    repository = DisputeRepository(db_connection)

    dispute = _make_dispute(
        tenant_id,
        service_act_id,
        provider_id,
    )

    created = repository.create(dispute)

    assert created.id is not None
    assert created.tenant_id == tenant_id
    assert created.service_act_id == service_act_id
    assert created.initiator_user_id == provider_id
    assert created.initiator_role == DisputeInitiatorRole.PROVIDER
    assert created.status == DisputeStatus.OPEN

    fetched = repository.get(tenant_id, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.reason == dispute.reason


def test_get_is_tenant_scoped(db_connection):
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    provider_a, recipient_a = _seed_users(db_connection, tenant_a)
    service_act_a = _seed_service_act(
        db_connection,
        tenant_a,
        provider_a,
        recipient_a,
    )

    repository = DisputeRepository(db_connection)

    dispute = repository.create(
        _make_dispute(
            tenant_a,
            service_act_a,
            provider_a,
        )
    )

    assert repository.get(tenant_a, dispute.id) is not None
    assert repository.get(tenant_b, dispute.id) is None


def test_list_by_tenant(db_connection):
    tenant_id = "tenant-a"
    provider_id, recipient_id = _seed_users(db_connection, tenant_id)

    service_act_id = _seed_service_act(
        db_connection,
        tenant_id,
        provider_id,
        recipient_id,
    )

    repository = DisputeRepository(db_connection)

    repository.create(
        _make_dispute(
            tenant_id,
            service_act_id,
            provider_id,
        )
    )

    disputes = repository.list_by_tenant(tenant_id)

    assert len(disputes) == 1
    assert disputes[0].service_act_id == service_act_id


def test_list_by_service_act(db_connection):
    tenant_id = "tenant-a"
    provider_id, recipient_id = _seed_users(db_connection, tenant_id)

    service_act_id = _seed_service_act(
        db_connection,
        tenant_id,
        provider_id,
        recipient_id,
    )

    repository = DisputeRepository(db_connection)

    dispute = repository.create(
        _make_dispute(
            tenant_id,
            service_act_id,
            provider_id,
        )
    )

    disputes = repository.list_by_service_act(
        tenant_id,
        service_act_id,
    )

    assert [item.id for item in disputes] == [dispute.id]


def test_list_by_initiator(db_connection):
    tenant_id = "tenant-a"
    provider_id, recipient_id = _seed_users(db_connection, tenant_id)

    service_act_id = _seed_service_act(
        db_connection,
        tenant_id,
        provider_id,
        recipient_id,
    )

    repository = DisputeRepository(db_connection)

    dispute = repository.create(
        _make_dispute(
            tenant_id,
            service_act_id,
            provider_id,
        )
    )

    disputes = repository.list_by_initiator(
        tenant_id,
        provider_id,
    )

    assert [item.id for item in disputes] == [dispute.id]


def test_dispute_resolution_round_trip(db_connection):
    tenant_id = "tenant-a"
    provider_id, recipient_id = _seed_users(db_connection, tenant_id)

    service_act_id = _seed_service_act(
        db_connection,
        tenant_id,
        provider_id,
        recipient_id,
    )

    repository = DisputeRepository(db_connection)

    dispute = Dispute(
        id=None,
        tenant_id=tenant_id,
        service_act_id=service_act_id,
        initiator_user_id=recipient_id,
        initiator_role=DisputeInitiatorRole.RECIPIENT,
        reason="The completed service did not meet the agreed standard.",
        status=DisputeStatus.RESOLVED,
        resolution=DisputeResolution.RECIPIENT_FAVORED,
        resolution_reason="Evidence supports the recipient.",
        resolved_by_user_id=recipient_id,
        resolved_at="2026-08-24 12:00:00",
    )

    created = repository.create(dispute)

    fetched = repository.get(
        tenant_id,
        created.id,
    )

    assert fetched.status == DisputeStatus.RESOLVED
    assert fetched.resolution == DisputeResolution.RECIPIENT_FAVORED
    assert fetched.resolution_reason == "Evidence supports the recipient."
    assert fetched.resolved_by_user_id == recipient_id
    assert fetched.resolved_at == "2026-08-24 12:00:00"
