from models.teacher_preacher_member import TeacherPreacherMemberLink
from services.teacher_preacher_member_service import (
    TeacherPreacherMemberService,
)


class FakeRepository:
    def __init__(self):
        self.created = []
        self.lookups = []

    def create(self, link):
        self.created.append(link)
        return link

    def get(
        self,
        tenant_id,
        teacher_preacher_id,
        membership_id,
    ):
        self.lookups.append(
            (
                tenant_id,
                teacher_preacher_id,
                membership_id,
            )
        )
        return TeacherPreacherMemberLink(
            tenant_id=tenant_id,
            teacher_preacher_id=teacher_preacher_id,
            membership_id=membership_id,
        )


def test_service_create_and_get():
    repository = FakeRepository()

    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    link = TeacherPreacherMemberLink(
        tenant_id="tenant-cmos",
        teacher_preacher_id=10,
        membership_id=20,
    )

    assert service.create(link) == link
    assert repository.created == [link]

    assert service.get(10, 20) == link
    assert repository.lookups == [
        ("tenant-cmos", 10, 20),
    ]


def test_service_rejects_tenant_mismatch():
    repository = FakeRepository()

    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id="tenant-cmos",
    )

    link = TeacherPreacherMemberLink(
        tenant_id="tenant-other",
        teacher_preacher_id=10,
        membership_id=20,
    )

    try:
        service.create(link)
        assert False, "expected tenant mismatch"
    except ValueError as exc:
        assert str(exc) == "teacher-preacher member tenant mismatch"

    assert repository.created == []


def test_missing_write_permission_rejected(db_connection):
    from services.teacher_preacher_member_service import (
        TeacherPreacherMemberService,
    )

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-cmos",),
    )
    db_connection.commit()

    repository = FakeRepository()
    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=db_connection,
        user_id="user-without-permission",
    )

    link = TeacherPreacherMemberLink(
        tenant_id="tenant-cmos",
        teacher_preacher_id=10,
        membership_id=20,
    )

    import pytest

    with pytest.raises(
        PermissionError,
        match="teacher_preacher_member.write",
    ):
        service.create(link)



def test_granted_write_permission_allows_create(db_connection):
    from services.teacher_preacher_member_service import (
        TeacherPreacherMemberService,
    )

    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )

    user_id = db_connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, "CMOS Writer", "member"),
    ).lastrowid

    role_id = db_connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "cmos_member_writer"),
    ).lastrowid

    permission_id = db_connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "teacher_preacher_member.write"),
    ).lastrowid

    db_connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        (tenant_id, user_id, role_id),
    )

    db_connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, role_id, permission_id),
    )

    db_connection.commit()

    repository = FakeRepository()
    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id=user_id,
    )

    link = TeacherPreacherMemberLink(
        tenant_id=tenant_id,
        teacher_preacher_id=10,
        membership_id=20,
    )

    assert service.create(link) == link
    assert repository.created == [link]


def test_granted_read_permission_allows_get(db_connection):
    from services.teacher_preacher_member_service import (
        TeacherPreacherMemberService,
    )

    tenant_id = "tenant-cmos"

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )

    user_id = db_connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        (tenant_id, "CMOS Reader", "member"),
    ).lastrowid

    role_id = db_connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "cmos_member_reader"),
    ).lastrowid

    permission_id = db_connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, status)
        VALUES (?, ?, 'active')
        """,
        (tenant_id, "teacher_preacher_member.read"),
    ).lastrowid

    db_connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        (tenant_id, user_id, role_id),
    )

    db_connection.execute(
        """
        INSERT INTO role_permissions (
            tenant_id,
            role_id,
            permission_id
        )
        VALUES (?, ?, ?)
        """,
        (tenant_id, role_id, permission_id),
    )

    db_connection.commit()

    repository = FakeRepository()
    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id=tenant_id,
        connection=db_connection,
        user_id=user_id,
    )

    expected = TeacherPreacherMemberLink(
        tenant_id=tenant_id,
        teacher_preacher_id=10,
        membership_id=20,
    )

    assert service.get(10, 20) == expected
    assert repository.lookups == [(tenant_id, 10, 20)]

def test_missing_read_permission_rejected(db_connection):
    from services.teacher_preacher_member_service import (
        TeacherPreacherMemberService,
    )

    db_connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-cmos",),
    )
    db_connection.commit()

    repository = FakeRepository()
    service = TeacherPreacherMemberService(
        repository=repository,
        tenant_id="tenant-cmos",
        connection=db_connection,
        user_id="user-without-permission",
    )

    import pytest

    with pytest.raises(
        PermissionError,
        match="teacher_preacher_member.read",
    ):
        service.get(10, 20)
