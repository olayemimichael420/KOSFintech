from models.service_act import ServiceAct, ServiceActStatus


def test_service_act_defaults_to_created():
    act = ServiceAct(
        id=None,
        tenant_id="tenant-001",
        provider_user_id=1,
        recipient_user_id=2,
        title="Mathematics tutoring",
        description="Provide three mathematics tutoring sessions.",
    )

    assert act.status == ServiceActStatus.CREATED
    assert act.id is None
    assert act.cancelled_at is None
    assert act.cancellation_reason is None


def test_service_act_status_values_are_stable():
    assert ServiceActStatus.CREATED.value == "created"
    assert ServiceActStatus.ACCEPTED.value == "accepted"
    assert ServiceActStatus.IN_PROGRESS.value == "in_progress"
    assert ServiceActStatus.SUBMITTED.value == "submitted"
    assert ServiceActStatus.COMPLETED.value == "completed"
    assert ServiceActStatus.CANCELLED.value == "cancelled"
