import pytest

from models.assessment_score import AssessmentScore
from services.assessment_score_service import AssessmentScoreService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.calls = []

    def create(self, assessment_score):
        self.created.append(assessment_score)
        return assessment_score

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

    def get(self, tenant_id, assessment_score_id):
        self.calls.append(("get", tenant_id, assessment_score_id))
        return None


def _assessment_score(tenant_id="tenant-a"):
    return AssessmentScore(
        id=None,
        tenant_id=tenant_id,
        assessment_id=17,
        membership_id=23,
        score=82,
        scored_date="2026-09-19",
    )


def test_record_accepts_assessment_score():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assessment_score = _assessment_score()

    assert service.record(assessment_score) == assessment_score
    assert repository.created == [assessment_score]


def test_record_rejects_tenant_mismatch():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    with pytest.raises(
        ValueError,
        match="assessment score tenant mismatch",
    ):
        service.record(_assessment_score(tenant_id="tenant-b"))

    assert repository.created == []


def test_list_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list() == []
    assert repository.calls == [
        ("list_by_tenant", "tenant-a"),
    ]


def test_list_by_assessment_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_assessment(17) == []
    assert repository.calls == [
        ("list_by_assessment", "tenant-a", 17),
    ]


def test_list_by_member_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.list_by_member(23) == []
    assert repository.calls == [
        ("list_by_member", "tenant-a", 23),
    ]


def test_get_uses_service_tenant():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assert service.get(7) is None
    assert repository.calls == [
        ("get", "tenant-a", 7),
    ]


def test_record_does_not_require_grade_result_or_progress():
    repository = FakeRepository()
    service = AssessmentScoreService(
        repository=repository,
        tenant_id="tenant-a",
    )

    assessment_score = _assessment_score()

    assert service.record(assessment_score) == assessment_score
    assert repository.created == [assessment_score]


def test_record_requires_write_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_score_repository import (
        AssessmentScoreRepository,
    )
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
            "Assessment Score User",
            "assessment-score@test",
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
            "assessment_score.read",
            "Read assessment scores",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentScoreService(
        repository=AssessmentScoreRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment_score.write",
    ):
        service.record(
            _assessment_score(tenant_id=tenant_id)
        )


def test_list_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_score_repository import (
        AssessmentScoreRepository,
    )
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
            "Assessment Score List User",
            "assessment-score-list@test",
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
            "assessment_score.write",
            "Write assessment scores",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentScoreService(
        repository=AssessmentScoreRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment_score.read",
    ):
        service.list()


def test_get_requires_read_permission(db_connection):
    from models.permission import Permission
    from models.role import Role
    from models.user_role import UserRoleLink
    from repositories.assessment_score_repository import (
        AssessmentScoreRepository,
    )
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
            "Assessment Score Get User",
            "assessment-score-get@test",
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
            "assessment_score.write",
            "Write assessment scores",
        )
    )

    UserRoleRepository(connection).create(
        UserRoleLink(tenant_id, user_id, role.id)
    )

    service = AssessmentScoreService(
        repository=AssessmentScoreRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="assessment_score.read",
    ):
        service.get(1)
