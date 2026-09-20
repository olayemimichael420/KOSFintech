import pytest
from models.assessment import Assessment
from services.assessment_service import AssessmentService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, assessment):
        self.created.append(assessment)
        return assessment

    def list_by_tenant(self, tenant_id):
        self.calls.append(("list_by_tenant", tenant_id))
        return []

    def list_by_content(self, tenant_id, teaching_content_id):
        self.calls.append(
            ("list_by_content", tenant_id, teaching_content_id)
        )
        return []

    def get(self, tenant_id, assessment_id):
        self.calls.append(("get", tenant_id, assessment_id))
        return None


def _assessment(tenant_id="tenant-a"):
    return Assessment(
        id=None,
        tenant_id=tenant_id,
        teaching_content_id=30,
        name="Understanding Review",
        description="Observable assessment activity.",
        assessment_date="2026-09-19",
    )


def test_record_accepts_assessment():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assessment = _assessment()

    assert service.record(assessment) == assessment
    assert repository.created == [assessment]


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    try:
        service.record(_assessment(tenant_id="tenant-b"))
        assert False, "expected tenant mismatch to be rejected"
    except ValueError as exc:
        assert str(exc) == "assessment tenant mismatch"

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_list_by_content_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_content(30) == []
    assert repository.calls == [
        ("list_by_content", "tenant-a", 30),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]


def test_record_does_not_require_learning_evidence_or_score():
    repository = FakeRepository()
    service = AssessmentService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assessment = _assessment()

    assert service.record(assessment) == assessment
    assert repository.created == [assessment]

def test_record_requires_write_permission(db_connection):
    import database
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_repository import AssessmentRepository
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
            "Assessment User",
            "assessment@test",
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
            "assessment.write",
            "Create assessments",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentService(
        repository=AssessmentRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment.write",
    ):
        service.record(
            Assessment(
                id=None,
                tenant_id=tenant_id,
                teaching_content_id=1,
                name="Assessment",
                assessment_date="2026-09-19",
            )
        )


def test_list_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_repository import AssessmentRepository
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
            "Assessment List User",
            "assessment-list@test",
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
            "assessment.write",
            "Create assessments",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentService(
        repository=AssessmentRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment.read",
    ):
        service.list()


def test_get_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_repository import AssessmentRepository
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
            "Assessment Get User",
            "assessment-get@test",
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
            "assessment.write",
            "Create assessments",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentService(
        repository=AssessmentRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment.read",
    ):
        service.get(1)
