import sqlite3

import pytest

from models.teacher import Teacher
from repositories.teacher_repository import TeacherRepository
from services.teacher_service import TeacherService


def create_schema(connection):
    connection.execute(
        """
        CREATE TABLE teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            qualification TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )
    connection.commit()


def test_teacher_service_creates_teacher_for_bound_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        service = TeacherService(
            TeacherRepository(connection),
            tenant_id="school-001",
        )

        teacher = Teacher(
            id=None,
            tenant_id="school-001",
            user_id=None,
            name="Teacher A",
            subject="Mathematics",
            qualification="B.Ed",
        )

        created = service.create(teacher)

        assert created.id is not None
        assert created.tenant_id == "school-001"

    finally:
        connection.close()


def test_teacher_service_rejects_cross_tenant_create():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        service = TeacherService(
            TeacherRepository(connection),
            tenant_id="school-001",
        )

        with pytest.raises(ValueError, match="teacher tenant mismatch"):
            service.create(
                Teacher(
                    id=None,
                    tenant_id="school-002",
                    user_id=None,
                    name="Teacher B",
                    subject="English",
                    qualification="B.A",
                )
            )

    finally:
        connection.close()


def test_teacher_service_get_is_bound_to_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        repository = TeacherRepository(connection)
        teacher = repository.create(
            Teacher(
                id=None,
                tenant_id="school-001",
                user_id=None,
                name="Teacher A",
                subject="Mathematics",
                qualification="B.Ed",
            )
        )

        service = TeacherService(
            repository,
            tenant_id="school-001",
        )

        assert service.get(teacher.id) is not None

        other_tenant_service = TeacherService(
            repository,
            tenant_id="school-002",
        )

        assert other_tenant_service.get(teacher.id) is None

    finally:
        connection.close()


def test_teacher_service_allows_authorized_write():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE user_roles (
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, user_id, role_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE role_permissions (
                tenant_id TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, role_id, permission_id)
            )
            """
        )

        user_id = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("school-001", "Teacher", "teacher@test", "member", "active"),
        ).lastrowid

        role_id = connection.execute(
            """
            INSERT INTO roles
                (tenant_id, name, description, status)
            VALUES (?, ?, ?, ?)
            """,
            ("school-001", "teacher", "Teacher", "active"),
        ).lastrowid

        permission_id = connection.execute(
            """
            INSERT INTO permissions
                (tenant_id, name, description, status)
            VALUES (?, ?, ?, ?)
            """,
            ("school-001", "teacher.write", "Create teachers", "active"),
        ).lastrowid

        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES (?, ?, ?)
            """,
            ("school-001", user_id, role_id),
        )

        connection.execute(
            """
            INSERT INTO role_permissions
                (tenant_id, role_id, permission_id)
            VALUES (?, ?, ?)
            """,
            ("school-001", role_id, permission_id),
        )
        connection.commit()

        service = TeacherService(
            TeacherRepository(connection),
            tenant_id="school-001",
            connection=connection,
            user_id=user_id,
        )

        created = service.create(
            Teacher(
                id=None,
                tenant_id="school-001",
                user_id=user_id,
                name="Teacher A",
                subject="Mathematics",
                qualification="B.Ed",
            )
        )

        assert created.id is not None

    finally:
        connection.close()


def test_teacher_service_denies_missing_write_permission():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE user_roles (
                tenant_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, user_id, role_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE role_permissions (
                tenant_id TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, role_id, permission_id)
            )
            """
        )

        user_id = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("school-001", "Teacher", "teacher@test", "member", "active"),
        ).lastrowid

        service = TeacherService(
            TeacherRepository(connection),
            tenant_id="school-001",
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(PermissionError, match="teacher.write"):
            service.create(
                Teacher(
                    id=None,
                    tenant_id="school-001",
                    user_id=user_id,
                    name="Teacher A",
                    subject="Mathematics",
                    qualification="B.Ed",
                )
            )

    finally:
        connection.close()



def test_teacher_service_list_is_bound_to_tenant():
    class Repository:
        def list(self, tenant_id):
            return [tenant_id]

    service = TeacherService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    assert service.list() == ["school-001"]



def test_teacher_service_list_is_bound_to_tenant():
    class Repository:
        def list(self, tenant_id):
            return [tenant_id]

    service = TeacherService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    assert service.list() == ["school-001"]



def test_teacher_service_list_denies_missing_read_permission():
    class Repository:
        def list(self, tenant_id):
            return []

    service = TeacherService(
        repository=Repository(),
        tenant_id="school-001",
        connection=None,
    )

    service.permission_service = type(
        "PermissionService",
        (),
        {"has_permission": lambda *args, **kwargs: False},
    )()
    service.user_id = 1

    with pytest.raises(PermissionError, match="missing permission: teacher.read"):
        service.list()
