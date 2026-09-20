from models.teaching_session_attendance import TeachingSessionAttendance
from services.teaching_session_attendance_service import (
    TeachingSessionAttendanceService,
)


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, attendance):
        self.created.append(attendance)
        return attendance

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return []

    def list_by_session(self, tenant_id, teaching_session_id):
        self.calls.append(
            ("list_by_session", tenant_id, teaching_session_id)
        )
        return []

    def list_by_member(self, tenant_id, membership_id):
        self.calls.append(
            ("list_by_member", tenant_id, membership_id)
        )
        return []

    def list_by_date(self, tenant_id, attendance_date):
        self.calls.append(
            ("list_by_date", tenant_id, attendance_date)
        )
        return []

    def get(self, tenant_id, attendance_id):
        self.calls.append(("get", tenant_id, attendance_id))
        return None


def _attendance(tenant_id="tenant-a", status="present"):
    return TeachingSessionAttendance(
        id=None,
        tenant_id=tenant_id,
        teaching_session_id=10,
        membership_id=20,
        attendance_date="2026-01-15",
        status=status,
    )


def test_record_accepts_allowed_statuses():
    for status in (
        "present",
        "absent",
        "late",
        "excused",
    ):
        repository = FakeRepository()
        service = TeachingSessionAttendanceService(
            repository=repository,
            tenant_id="tenant-a",
        )

        attendance = _attendance(status=status)

        assert service.record(attendance) == attendance
        assert repository.created == [attendance]


def test_record_rejects_invalid_status():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    try:
        service.record(_attendance(status="unknown"))
        assert False, "expected invalid status to be rejected"
    except ValueError as exc:
        assert str(exc) == "invalid teaching session attendance status"

    assert repository.created == []


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    try:
        service.record(_attendance(tenant_id="tenant-b"))
        assert False, "expected tenant mismatch to be rejected"
    except ValueError as exc:
        assert str(exc) == "teaching session attendance tenant mismatch"

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_list_by_session_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_session(10) == []
    assert repository.calls == [
        ("list_by_session", "tenant-a", 10),
    ]


def test_list_by_member_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_member(20) == []
    assert repository.calls == [
        ("list_by_member", "tenant-a", 20),
    ]


def test_list_by_date_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_date("2026-01-15") == []
    assert repository.calls == [
        ("list_by_date", "tenant-a", "2026-01-15"),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = TeachingSessionAttendanceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]
