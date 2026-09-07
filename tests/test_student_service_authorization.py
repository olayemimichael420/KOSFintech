import sqlite3

import pytest

from models.student import Student
from repositories.student_repository import StudentRepository
from services.student_service import StudentService


def create_schema(connection):
    connection.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        );

        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE user_roles (
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, user_id, role_id)
        );

        CREATE TABLE role_permissions (
            tenant_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (tenant_id, role_id, permission_id)
        );

        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            age INTEGER,
            guardian_id INTEGER,
            enrollment_date DATE,
            status TEXT DEFAULT 'active'
        );
        """
    )
    connection.commit()


def seed_user(connection, *, with_student_read):
    cursor = connection.execute(
        """
        INSERT INTO users (tenant_id, name, email, role, status)
        VALUES ('tenant-a', 'Alice', ?, 'member', 'active')
        """,
        (
            "alice@example.test"
            if with_student_read
            else "bob@example.test",
        ),
    )
    user_id = cursor.lastrowid

    role_id = connection.execute(
        """
        INSERT INTO roles (tenant_id, name, status)
        VALUES ('tenant-a', 'teacher', 'active')
        """
    ).lastrowid

    if with_student_read:
        permission_id = connection.execute(
            """
            INSERT INTO permissions (tenant_id, name, status)
            VALUES ('tenant-a', 'student.read', 'active')
            """
        ).lastrowid

        connection.execute(
            """
            INSERT INTO user_roles (tenant_id, user_id, role_id)
            VALUES ('tenant-a', ?, ?)
            """,
            (user_id, role_id),
        )

        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id,
                role_id,
                permission_id
            )
            VALUES ('tenant-a', ?, ?)
            """,
            (role_id, permission_id),
        )

    connection.commit()
    return user_id


def seed_student(connection):
    repository = StudentRepository(connection)
    return repository.create(
        Student(
            id=None,
            tenant_id="tenant-a",
            user_id=None,
            name="Student A",
            class_name="JSS 1",
            age=12,
            guardian_id=None,
            enrollment_date="2026-09-06",
        )
    )


def test_authorized_user_can_execute_student_read():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)
        user_id = seed_user(connection, with_student_read=True)
        student = seed_student(connection)

        service = StudentService(
            StudentRepository(connection),
            tenant_id="tenant-a",
            connection=connection,
            user_id=user_id,
        )

        result = service.get(student.id)

        assert result is not None
        assert result.id == student.id
        assert result.tenant_id == "tenant-a"

    finally:
        connection.close()


def test_user_without_student_read_is_denied():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)
        user_id = seed_user(connection, with_student_read=False)
        student = seed_student(connection)

        service = StudentService(
            StudentRepository(connection),
            tenant_id="tenant-a",
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(
            PermissionError,
            match="missing permission: student.read",
        ):
            service.get(student.id)

    finally:
        connection.close()

def test_user_without_student_read_is_denied_for_list():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_schema(connection)

    user_id = seed_user(connection, with_student_read=False)

    service = StudentService(
        repository=StudentRepository(connection),
        tenant_id="tenant-a",
        connection=connection,
        user_id=user_id,
    )

    with pytest.raises(PermissionError, match="missing permission: student.read"):
        service.list()

    connection.close()

def test_user_with_student_write_can_create():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)
        user_id = seed_user(connection, with_student_read=True)

        permission_id = connection.execute(
            """
            INSERT INTO permissions (tenant_id, name, status)
            VALUES ('tenant-a', 'student.write', 'active')
            """
        ).lastrowid

        role_id = connection.execute(
            """
            SELECT id FROM roles
            WHERE tenant_id = 'tenant-a' AND name = 'teacher'
            """
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id, role_id, permission_id
            )
            VALUES ('tenant-a', ?, ?)
            """,
            (role_id, permission_id),
        )
        connection.commit()

        service = StudentService(
            StudentRepository(connection),
            tenant_id="tenant-a",
            connection=connection,
            user_id=user_id,
        )

        created = service.create(
            Student(
                id=None,
                tenant_id="tenant-a",
                user_id=None,
                name="Student Write",
                class_name="JSS 1",
                age=12,
                guardian_id=None,
                enrollment_date="2026-09-07",
            )
        )

        assert created.id is not None
        assert created.tenant_id == "tenant-a"

    finally:
        connection.close()


def test_user_without_student_write_is_denied_for_create():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)
        user_id = seed_user(connection, with_student_read=True)

        service = StudentService(
            StudentRepository(connection),
            tenant_id="tenant-a",
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(
            PermissionError,
            match="missing permission: student.write",
        ):
            service.create(
                Student(
                    id=None,
                    tenant_id="tenant-a",
                    user_id=None,
                    name="Unauthorized Student",
                    class_name="JSS 1",
                    age=12,
                    guardian_id=None,
                    enrollment_date="2026-09-07",
                )
            )

    finally:
        connection.close()
