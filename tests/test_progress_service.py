import pytest

from models.progress import Progress
from services.progress_service import ProgressService


class StubPermissionService:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []

    def has_permission(self, **kwargs):
        self.calls.append(kwargs)
        return self.allowed


class StubRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, progress):
        self.created.append(progress)
        return progress

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return ["tenant-progress"]

    def list_by_member(self, tenant_id, membership_id):
        self.calls.append(("list_by_member", tenant_id, membership_id))
        return ["member-progress"]

    def list_by_content(self, tenant_id, teaching_content_id):
        self.calls.append(
            ("list_by_content", tenant_id, teaching_content_id)
        )
        return ["content-progress"]

    def get(self, tenant_id, progress_id):
        self.calls.append(("get", tenant_id, progress_id))
        return "progress"


def _progress(tenant_id="tenant-cmos"):
    return Progress(
        id=None,
        tenant_id=tenant_id,
        membership_id=1,
        teaching_content_id=1,
        progress_date="2026-09-19",
        description="Recorded learning development",
    )


def test_record_delegates_to_repository():
    repository = StubRepository()
    service = ProgressService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    progress = _progress()
    assert service.record(progress) == progress
    assert repository.created == [progress]


def test_record_rejects_tenant_mismatch():
    service = ProgressService(
        repository=StubRepository(),
        tenant_id="tenant-cmos",
    )

    with pytest.raises(ValueError, match="progress tenant mismatch"):
        service.record(_progress("other-tenant"))


def test_list_is_tenant_scoped():
    repository = StubRepository()
    service = ProgressService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    assert service.list() == ["tenant-progress"]
    assert repository.calls == [
        ("list_by_tenant", "tenant-cmos")
    ]


def test_list_by_member_is_tenant_scoped():
    repository = StubRepository()
    service = ProgressService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    assert service.list_by_member(7) == ["member-progress"]
    assert repository.calls == [
        ("list_by_member", "tenant-cmos", 7)
    ]


def test_list_by_content_is_tenant_scoped():
    repository = StubRepository()
    service = ProgressService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    assert service.list_by_content(9) == ["content-progress"]
    assert repository.calls == [
        ("list_by_content", "tenant-cmos", 9)
    ]


def test_get_is_tenant_scoped():
    repository = StubRepository()
    service = ProgressService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    assert service.get(11) == "progress"
    assert repository.calls == [
        ("get", "tenant-cmos", 11)
    ]


def test_write_permission_is_required():
    service = ProgressService(
        repository=StubRepository(),
        tenant_id="tenant-cmos",
        connection=object(),
        user_id=42,
    )
    service.permission_service = StubPermissionService(allowed=False)

    with pytest.raises(PermissionError, match="progress.write"):
        service.record(_progress())


def test_read_permission_is_required():
    service = ProgressService(
        repository=StubRepository(),
        tenant_id="tenant-cmos",
        connection=object(),
        user_id=42,
    )
    service.permission_service = StubPermissionService(allowed=False)

    with pytest.raises(PermissionError, match="progress.read"):
        service.list()


def test_permission_context_is_tenant_bound():
    service = ProgressService(
        repository=StubRepository(),
        tenant_id="tenant-cmos",
        connection=object(),
        user_id=42,
    )
    permission_service = StubPermissionService(allowed=True)
    service.permission_service = permission_service

    service.list()

    assert permission_service.calls == [
        {
            "user_id": 42,
            "permission_name": "progress.read",
            "tenant_id": "tenant-cmos",
        }
    ]
