import pytest

from models.grade import Grade
from services.grade_service import GradeService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, grade):
        self.created.append(grade)
        return grade

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return []

    def get(self, tenant_id, grade_id):
        self.calls.append(("get", tenant_id, grade_id))
        return None


def _grade(tenant_id="tenant-a"):
    return Grade(
        id=None,
        tenant_id=tenant_id,
        name="A",
        description="Excellent",
        minimum_score=80,
        maximum_score=100,
    )


def test_record_accepts_grade():
    repository = FakeRepository()
    service = GradeService(
        repository=repository,
        tenant_id="tenant-a",
    )

    grade = _grade()

    assert service.record(grade) == grade
    assert repository.created == [grade]


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = GradeService(
        repository=repository,
        tenant_id="tenant-a",
    )

    with pytest.raises(
        ValueError,
        match="grade tenant mismatch",
    ):
        service.record(_grade(tenant_id="tenant-b"))

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = GradeService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = GradeService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]


def test_record_does_not_require_result_or_progress():
    repository = FakeRepository()
    service = GradeService(
        repository=repository,
        tenant_id="tenant-a",
    )

    grade = _grade()

    assert service.record(grade) == grade
    assert repository.created == [grade]


def test_record_requires_write_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.grade_repository import GradeRepository
    from repositories.permission_repository import PermissionRepository
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
            "Grade User",
            "grade@test",
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
            "grade.write",
            "Create grades",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = GradeService(
        repository=GradeRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="grade.write",
    ):
        service.record(
            Grade(
                id=None,
                tenant_id=tenant_id,
                name="A",
                minimum_score=80,
                maximum_score=100,
            )
        )


def test_list_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.grade_repository import GradeRepository
    from repositories.permission_repository import PermissionRepository
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
            "Grade List User",
            "grade-list@test",
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
            "grade.write",
            "Create grades",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = GradeService(
        repository=GradeRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="grade.read",
    ):
        service.list()


def test_get_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.grade_repository import GradeRepository
    from repositories.permission_repository import PermissionRepository
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
            "Grade Get User",
            "grade-get@test",
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
            "grade.write",
            "Create grades",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = GradeService(
        repository=GradeRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="grade.read",
    ):
        service.get(1)
