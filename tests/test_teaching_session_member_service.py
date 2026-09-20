from models.teaching_session_member import TeachingSessionMemberLink
from services.teaching_session_member_service import TeachingSessionMemberService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.items = {}

    def create(self, link):
        self.created.append(link)
        key = (
            link.tenant_id,
            link.teaching_session_id,
            link.membership_id,
        )
        self.items[key] = link
        return link

    def get(
        self,
        tenant_id,
        teaching_session_id,
        membership_id,
    ):
        return self.items.get(
            (
                tenant_id,
                teaching_session_id,
                membership_id,
            )
        )


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


def make_link(tenant_id):
    return TeachingSessionMemberLink(
        tenant_id=tenant_id,
        teaching_session_id=101,
        membership_id=201,
    )


def test_create_delegates_to_repository():
    repository = FakeRepository()

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
    )

    link = service.create(make_link("tenant-a"))

    assert link.tenant_id == "tenant-a"
    assert repository.created == [link]


def test_create_rejects_tenant_mismatch():
    repository = FakeRepository()

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
    )

    try:
        service.create(make_link("tenant-b"))
    except ValueError as exc:
        assert str(exc) == "teaching session member tenant mismatch"
    else:
        raise AssertionError("expected tenant mismatch")


def test_get_delegates_with_service_tenant():
    repository = FakeRepository()
    link = repository.create(make_link("tenant-a"))

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(
        link.teaching_session_id,
        link.membership_id,
    ) == link


def test_missing_write_permission_rejected():
    repository = FakeRepository()

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService()

    try:
        service.create(make_link("tenant-a"))
    except PermissionError as exc:
        assert str(exc) == (
            "missing permission: "
            "teaching_session_member.write"
        )
    else:
        raise AssertionError("expected write permission failure")


def test_missing_read_permission_rejected():
    repository = FakeRepository()
    link = repository.create(make_link("tenant-a"))

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService()

    try:
        service.get(
            link.teaching_session_id,
            link.membership_id,
        )
    except PermissionError as exc:
        assert str(exc) == (
            "missing permission: "
            "teaching_session_member.read"
        )
    else:
        raise AssertionError("expected read permission failure")


def test_granted_write_permission_allows_create():
    repository = FakeRepository()

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService(
        {"teaching_session_member.write"}
    )

    link = service.create(make_link("tenant-a"))

    assert link in repository.created


def test_granted_read_permission_allows_get():
    repository = FakeRepository()
    link = repository.create(make_link("tenant-a"))

    service = TeachingSessionMemberService(
        repository=repository,
        tenant_id="tenant-a",
        connection=object(),
        user_id=1,
    )
    service.permission_service = FakePermissionService(
        {"teaching_session_member.read"}
    )

    assert service.get(
        link.teaching_session_id,
        link.membership_id,
    ) == link
