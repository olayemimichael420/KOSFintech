from models.learning_evidence import LearningEvidence
from services.learning_evidence_service import LearningEvidenceService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, evidence):
        self.created.append(evidence)
        return evidence

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return []

    def list_by_member(self, tenant_id, membership_id):
        self.calls.append(("list_by_member", tenant_id, membership_id))
        return []

    def list_by_content(self, tenant_id, teaching_content_id):
        self.calls.append(
            ("list_by_content", tenant_id, teaching_content_id)
        )
        return []

    def get(self, tenant_id, evidence_id):
        self.calls.append(("get", tenant_id, evidence_id))
        return None


def _evidence(tenant_id="tenant-a"):
    return LearningEvidence(
        id=None,
        tenant_id=tenant_id,
        membership_id=20,
        teaching_content_id=30,
        evidence_date="2026-09-19",
        description="Member submitted a written reflection.",
        remark="Observable learning evidence.",
    )


def test_record_accepts_learning_evidence():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    evidence = _evidence()

    assert service.record(evidence) == evidence
    assert repository.created == [evidence]


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    try:
        service.record(_evidence(tenant_id="tenant-b"))
        assert False, "expected tenant mismatch to be rejected"
    except ValueError as exc:
        assert str(exc) == "learning evidence tenant mismatch"

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_list_by_member_uses_service_tenant():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_member(20) == []
    assert repository.calls == [
        ("list_by_member", "tenant-a", 20),
    ]


def test_list_by_content_uses_service_tenant():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_content(30) == []
    assert repository.calls == [
        ("list_by_content", "tenant-a", 30),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]


def test_record_does_not_require_attendance_or_assessment():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
    )

    evidence = _evidence()

    assert service.record(evidence) == evidence
    assert repository.created == [evidence]

class FakePermissionService:
    def __init__(self, granted=None):
        self.granted = set(granted or [])

    def has_permission(
        self,
        user_id,
        permission_name,
        tenant_id,
    ):
        return permission_name in self.granted


def test_record_requires_write_permission():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService()

    try:
        service.record(_evidence())
    except PermissionError as exc:
        assert str(exc) == "missing permission: learning_evidence.write"
    else:
        raise AssertionError("expected write permission failure")

    assert repository.created == []


def test_record_allows_granted_write_permission():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService(
        {"learning_evidence.write"}
    )

    evidence = _evidence()

    assert service.record(evidence) == evidence
    assert repository.created == [evidence]


def test_list_requires_read_permission():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService()

    try:
        service.list()
    except PermissionError as exc:
        assert str(exc) == "missing permission: learning_evidence.read"
    else:
        raise AssertionError("expected read permission failure")


def test_list_allows_granted_read_permission():
    repository = FakeRepository()
    service = LearningEvidenceService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService(
        {"learning_evidence.read"}
    )

    assert service.list() == []
