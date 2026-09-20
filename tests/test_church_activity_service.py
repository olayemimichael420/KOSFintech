import uuid

import pytest
from database import get_connection, init_db
from models.church_activity import ChurchActivity
from repositories.church_activity_repository import ChurchActivityRepository
from services.church_activity_service import ChurchActivityService


def _tenant(connection, tenant_id):
    connection.execute("INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')", (tenant_id,))
    connection.commit()


@pytest.fixture
def service():
    init_db()
    connection = get_connection()
    tenant_id = f"church-activity-service-{uuid.uuid4().hex}"
    try:
        _tenant(connection, tenant_id)
        repository = ChurchActivityRepository(connection)
        yield (
            ChurchActivityService(
                repository=repository,
                tenant_id=tenant_id,
                connection=None,
                user_id=None,
            ),
            tenant_id,
        )
    finally:
        connection.close()


def test_create_and_get_activity(service):
    activity_service, tenant_id = service
    created = activity_service.create(
        ChurchActivity(
            id=None,
            tenant_id=tenant_id,
            name="Sunday Worship",
            activity_type="worship",
        )
    )
    loaded = activity_service.get(created.id)
    assert loaded is not None
    assert loaded.name == "Sunday Worship"
    assert loaded.tenant_id == tenant_id


def test_create_rejects_tenant_mismatch(service):
    activity_service, tenant_id = service
    with pytest.raises(ValueError, match="tenant mismatch"):
        activity_service.create(
            ChurchActivity(
                id=None,
                tenant_id=f"other-{uuid.uuid4().hex}",
                name="Bible Study",
                activity_type="teaching",
            )
        )


def test_list_is_tenant_scoped(service):
    activity_service, tenant_id = service
    activity_service.create(
        ChurchActivity(
            id=None,
            tenant_id=tenant_id,
            name="Prayer",
            activity_type="prayer",
        )
    )
    activities = activity_service.list()
    assert len(activities) == 1
    assert activities[0].tenant_id == tenant_id
    assert activities[0].name == "Prayer"
