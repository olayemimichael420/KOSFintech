import sqlite3

import pytest

from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole
from repositories.teacher_preacher_repository import TeacherPreacherRepository
from services.teacher_preacher_service import TeacherPreacherService


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _create_person(connection, name):
    return connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (name,),
    ).lastrowid


def test_service_creates_capacity_for_bound_tenant(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    person_id = _create_person(connection, "Teacher One")

    service = TeacherPreacherService(
        TeacherPreacherRepository(connection),
        tenant_id="tenant-001",
    )

    capacity = service.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    assert capacity.id is not None
    assert capacity.tenant_id == "tenant-001"


def test_service_rejects_cross_tenant_create(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")
    person_id = _create_person(connection, "Teacher One")

    service = TeacherPreacherService(
        TeacherPreacherRepository(connection),
        tenant_id="tenant-001",
    )

    with pytest.raises(
        ValueError,
        match="teacher/preacher tenant mismatch",
    ):
        service.create(
            TeacherPreacher(
                id=None,
                tenant_id="tenant-002",
                person_id=person_id,
                role=TeacherPreacherRole.TEACHER,
            )
        )


def test_service_get_is_tenant_bound(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")
    person_id = _create_person(connection, "Teacher One")

    repository = TeacherPreacherRepository(connection)
    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_id,
            role=TeacherPreacherRole.PREACHER,
        )
    )

    service = TeacherPreacherService(
        repository,
        tenant_id="tenant-001",
    )
    other_service = TeacherPreacherService(
        repository,
        tenant_id="tenant-002",
    )

    assert service.get(capacity.id) == capacity
    assert other_service.get(capacity.id) is None


def test_service_list_is_tenant_bound(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    _create_tenant(connection, "tenant-002")
    person_one = _create_person(connection, "Teacher One")
    person_two = _create_person(connection, "Teacher Two")

    repository = TeacherPreacherRepository(connection)

    repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_one,
            role=TeacherPreacherRole.TEACHER,
        )
    )
    repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-002",
            person_id=person_two,
            role=TeacherPreacherRole.PREACHER,
        )
    )

    service = TeacherPreacherService(
        repository,
        tenant_id="tenant-001",
    )

    result = service.list()

    assert len(result) == 1
    assert result[0].person_id == person_one


def test_service_denies_missing_write_permission(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    person_id = _create_person(connection, "Teacher One")

    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "User One", "member"),
    ).lastrowid
    connection.commit()

    service = TeacherPreacherService(
        TeacherPreacherRepository(connection),
        tenant_id="tenant-001",
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(PermissionError, match="teacher_preacher.write"):
        service.create(
            TeacherPreacher(
                id=None,
                tenant_id="tenant-001",
                person_id=person_id,
                role=TeacherPreacherRole.TEACHER,
            )
        )


def test_service_allows_authorized_write(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    person_id = _create_person(connection, "Teacher One")

    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "User One", "member"),
    ).lastrowid

    role_id = connection.execute(
        """
        INSERT INTO roles (tenant_id, name, description, status)
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-001", "teacher_admin", "Teacher admin", "active"),
    ).lastrowid

    permission_id = connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, description, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            "tenant-001",
            "teacher_preacher.write",
            "Create teacher/preacher capacity",
            "active",
        ),
    ).lastrowid

    connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", user_id, role_id),
    )
    connection.execute(
        """
        INSERT INTO role_permissions (tenant_id, role_id, permission_id)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", role_id, permission_id),
    )
    connection.commit()

    service = TeacherPreacherService(
        TeacherPreacherRepository(connection),
        tenant_id="tenant-001",
        connection=connection,
        user_id=user_id,
    )

    created = service.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_id,
            role=TeacherPreacherRole.TEACHER_PREACHER,
        )
    )

    assert created.id is not None


def test_service_denies_missing_read_permission(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    person_id = _create_person(connection, "Teacher One")

    repository = TeacherPreacherRepository(connection)
    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "User One", "member"),
    ).lastrowid
    connection.commit()

    service = TeacherPreacherService(
        repository,
        tenant_id="tenant-001",
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(PermissionError, match="teacher_preacher.read"):
        service.get(capacity.id)


def test_service_allows_authorized_read(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    person_id = _create_person(connection, "Teacher One")

    repository = TeacherPreacherRepository(connection)
    capacity = repository.create(
        TeacherPreacher(
            id=None,
            tenant_id="tenant-001",
            person_id=person_id,
            role=TeacherPreacherRole.TEACHER,
        )
    )

    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "User One", "member"),
    ).lastrowid

    role_id = connection.execute(
        """
        INSERT INTO roles (tenant_id, name, description, status)
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-001", "teacher_viewer", "Teacher viewer", "active"),
    ).lastrowid

    permission_id = connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, description, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            "tenant-001",
            "teacher_preacher.read",
            "Read teacher/preacher capacity",
            "active",
        ),
    ).lastrowid

    connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", user_id, role_id),
    )
    connection.execute(
        """
        INSERT INTO role_permissions (tenant_id, role_id, permission_id)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", role_id, permission_id),
    )
    connection.commit()

    service = TeacherPreacherService(
        repository,
        tenant_id="tenant-001",
        connection=connection,
        user_id=user_id,
    )

    assert service.get(capacity.id) == capacity


def test_service_requires_permission_for_list(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-001")
    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role)
        VALUES (?, ?, ?)
        """,
        ("tenant-001", "User One", "member"),
    ).lastrowid
    connection.commit()

    service = TeacherPreacherService(
        TeacherPreacherRepository(connection),
        tenant_id="tenant-001",
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(PermissionError, match="teacher_preacher.read"):
        service.list()
