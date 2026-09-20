import pytest

from models.result import Result
from services.result_service import ResultService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, result):
        self.created.append(result)
        return result

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return []

    def list_by_assessment(self, tenant_id, assessment_id):
        self.calls.append(
            ("list_by_assessment", tenant_id, assessment_id)
        )
        return []

    def list_by_member(self, tenant_id, membership_id):
        self.calls.append(
            ("list_by_member", tenant_id, membership_id)
        )
        return []

    def get(self, tenant_id, result_id):
        self.calls.append(("get", tenant_id, result_id))
        return None


def _result(tenant_id="tenant-a"):
    return Result(
        id=None,
        tenant_id=tenant_id,
        assessment_id=17,
        membership_id=23,
        grade_id=5,
        result="Demonstrated understanding of the teaching content",
        result_date="2026-09-19",
    )


def test_record_accepts_result():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    result = _result()

    assert service.record(result) == result
    assert repository.created == [result]


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    with pytest.raises(
        ValueError,
        match="result tenant mismatch",
    ):
        service.record(_result(tenant_id="tenant-b"))

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_list_by_assessment_uses_service_tenant():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_assessment(17) == []
    assert repository.calls == [
        ("list_by_assessment", "tenant-a", 17),
    ]


def test_list_by_member_uses_service_tenant():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_member(23) == []
    assert repository.calls == [
        ("list_by_member", "tenant-a", 23),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]


def test_record_does_not_require_score_or_progress():
    repository = FakeRepository()
    service = ResultService(
        repository=repository,
        tenant_id="tenant-a",
    )

    result = _result()

    assert service.record(result) == result
    assert repository.created == [result]


def test_record_requires_write_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.role_repository import RoleRepository
    from repositories.result_repository import ResultRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = db_connection
    tenant_id = "tenant-auth"

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        (tenant_id,),
    )

    cursor = connection.execute(
        """
        INSERT INTO users
            (tenant_id, name, email, role, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            "Result User",
            "result@test",
            "member",
            "active",
        ),
    )
    user_id = cursor.lastrowid

    role = RoleRepository(connection).create(
        Role(None, tenant_id, "teacher", "Teacher")
    )

    PermissionRepository(connection).create(
        Permission(
            None,
            tenant_id,
            "result.read",
            "Read results",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = ResultService(
        repository=ResultRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="result.write",
    ):
        service.record(_result(tenant_id=tenant_id))


def test_list_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.result_repository import ResultRepository
    from repositories.role_repository import RoleRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = db_connection
    tenant_id = "tenant-auth"

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        (tenant_id,),
    )

    cursor = connection.execute(
        """
        INSERT INTO users
            (tenant_id, name, email, role, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            "Result List User",
            "result-list@test",
            "member",
            "active",
        ),
    )
    user_id = cursor.lastrowid

    role = RoleRepository(connection).create(
        Role(None, tenant_id, "teacher", "Teacher")
    )

    PermissionRepository(connection).create(
        Permission(
            None,
            tenant_id,
            "result.write",
            "Write results",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = ResultService(
        repository=ResultRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="result.read",
    ):
        service.list()


def test_get_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.permission_repository import PermissionRepository
    from repositories.result_repository import ResultRepository
    from repositories.role_repository import RoleRepository
    from repositories.user_role_repository import UserRoleRepository

    connection = db_connection
    tenant_id = "tenant-auth"

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        (tenant_id,),
    )

    cursor = connection.execute(
        """
        INSERT INTO users
            (tenant_id, name, email, role, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            "Result Get User",
            "result-get@test",
            "member",
            "active",
        ),
    )
    user_id = cursor.lastrowid

    role = RoleRepository(connection).create(
        Role(None, tenant_id, "teacher", "Teacher")
    )

    PermissionRepository(connection).create(
        Permission(
            None,
            tenant_id,
            "result.write",
            "Write results",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = ResultService(
        repository=ResultRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="result.read",
    ):
        service.get(1)
