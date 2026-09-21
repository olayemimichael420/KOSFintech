import pytest

from models.teaching_session_subject import TeachingSessionSubject
from services.teaching_session_subject_service import TeachingSessionSubjectService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.items = {}

    def create(self, offering):
        self.created.append(offering)
        item = TeachingSessionSubject(
            id=len(self.created),
            tenant_id=offering.tenant_id,
            teaching_session_id=offering.teaching_session_id,
            teaching_subject_id=offering.teaching_subject_id,
            status=offering.status,
        )
        self.items[item.id] = item
        return item

    def get(self, tenant_id, offering_id):
        item = self.items.get(offering_id)
        if item is None or item.tenant_id != tenant_id:
            return None
        return item

    def list(self, tenant_id, teaching_session_id):
        return [
            item
            for item in self.items.values()
            if item.tenant_id == tenant_id
            and item.teaching_session_id == teaching_session_id
        ]


def make_offering(tenant_id):
    return TeachingSessionSubject(
        id=None,
        tenant_id=tenant_id,
        teaching_session_id=101,
        teaching_subject_id=201,
    )


def test_create_delegates_to_repository():
    repository = FakeRepository()
    service = TeachingSessionSubjectService(
        repository=repository,
        tenant_id="tenant-a",
    )

    created = service.create(make_offering("tenant-a"))

    assert created.id is not None
    assert created.tenant_id == "tenant-a"
    assert repository.created[0].tenant_id == "tenant-a"


def test_create_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = TeachingSessionSubjectService(
        repository=repository,
        tenant_id="tenant-a",
    )

    with pytest.raises(
        ValueError,
        match="teaching session subject tenant mismatch",
    ):
        service.create(make_offering("tenant-b"))


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionSubjectService(
        repository=repository,
        tenant_id="tenant-a",
    )

    created = service.create(make_offering("tenant-a"))

    assert service.get(created.id) == created


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionSubjectService(
        repository=repository,
        tenant_id="tenant-a",
    )

    created = service.create(make_offering("tenant-a"))

    assert service.list(101) == [created]


def test_missing_write_permission_is_rejected(db_connection):
    service = TeachingSessionSubjectService(
        repository=FakeRepository(),
        tenant_id="tenant-a",
        connection=db_connection,
        user_id="user-without-permission",
    )

    with pytest.raises(
        PermissionError,
        match="teaching_session_subject.write",
    ):
        service.create(make_offering("tenant-a"))


def test_missing_read_permission_is_rejected(db_connection):
    service = TeachingSessionSubjectService(
        repository=FakeRepository(),
        tenant_id="tenant-a",
        connection=db_connection,
        user_id="user-without-permission",
    )

    with pytest.raises(
        PermissionError,
        match="teaching_session_subject.read",
    ):
        service.get(1)

    with pytest.raises(
        PermissionError,
        match="teaching_session_subject.read",
    ):
        service.list(101)
