import sqlite3
import pytest

from models.attendance import Attendance
from repositories.attendance_repository import AttendanceRepository
from services.attendance_service import AttendanceService


def test_attendance_service_records_valid_status():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(AttendanceRepository(connection), tenant_id="school-001")

    result = service.record(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-29",
            status="late",
        )
    )

    assert result.id is not None
    assert result.status == "late"

    connection.close()


def test_attendance_service_rejects_invalid_status():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(AttendanceRepository(connection), tenant_id="school-001")

    try:
        service.record(
            Attendance(
                id=None,
                tenant_id="school-001",
                student_id=1,
                attendance_date="2026-08-29",
                status="invalid",
            )
        )
    except ValueError as exc:
        assert str(exc) == "invalid attendance status"
    else:
        raise AssertionError("invalid attendance status was accepted")

    connection.close()


def test_attendance_service_rejects_cross_tenant_write():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(
        AttendanceRepository(connection),
        tenant_id="school-001",
    )

    try:
        try:
            service.record(
                Attendance(
                    id=None,
                    tenant_id="school-002",
                    student_id=1,
                    attendance_date="2026-08-29",
                    status="present",
                )
            )
        except ValueError as exc:
            assert str(exc) == "attendance tenant mismatch"
        else:
            raise AssertionError(
                "cross-tenant attendance write was accepted"
            )
    finally:
        connection.close()


def test_attendance_service_read_uses_bound_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    first = repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-29",
            status="present",
        )
    )

    second = repository.create(
        Attendance(
            id=None,
            tenant_id="school-002",
            student_id=1,
            attendance_date="2026-08-29",
            status="absent",
        )
    )

    service = AttendanceService(
        repository,
        tenant_id="school-001",
    )

    assert service.get(first.id) is not None
    assert service.get(second.id) is None

    connection.close()


def test_attendance_service_lists_only_bound_tenant_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-29",
            status="present",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-002",
            student_id=2,
            attendance_date="2026-08-29",
            status="absent",
        )
    )

    service = AttendanceService(
        repository,
        tenant_id="school-001",
    )

    results = service.list()

    assert len(results) == 1
    assert results[0].tenant_id == "school-001"
    assert results[0].student_id == 1

    connection.close()

def test_attendance_service_lists_empty_for_tenant_with_no_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(
        AttendanceRepository(connection),
        tenant_id="school-empty",
    )

    results = service.list()

    assert results == []

    connection.close()

def test_attendance_service_lists_student_records_with_bound_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-30",
            status="present",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-29",
            status="late",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=2,
            attendance_date="2026-08-29",
            status="absent",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-002",
            student_id=1,
            attendance_date="2026-08-28",
            status="excused",
        )
    )

    service = AttendanceService(
        repository,
        tenant_id="school-001",
    )

    results = service.list_by_student(1)

    assert len(results) == 2
    assert all(item.tenant_id == "school-001" for item in results)
    assert all(item.student_id == 1 for item in results)
    assert [item.attendance_date for item in results] == [
        "2026-08-29",
        "2026-08-30",
    ]

    connection.close()


def test_attendance_service_lists_empty_for_student_with_no_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(
        AttendanceRepository(connection),
        tenant_id="school-001",
    )

    results = service.list_by_student(999)

    assert results == []

    connection.close()

def test_attendance_service_lists_only_bound_tenant_records_for_date():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=1,
            attendance_date="2026-08-30",
            status="present",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-002",
            student_id=2,
            attendance_date="2026-08-30",
            status="absent",
        )
    )

    repository.create(
        Attendance(
            id=None,
            tenant_id="school-001",
            student_id=3,
            attendance_date="2026-08-29",
            status="late",
        )
    )

    service = AttendanceService(
        repository,
        tenant_id="school-001",
    )

    results = service.list_by_date("2026-08-30")

    assert len(results) == 1
    assert results[0].tenant_id == "school-001"
    assert results[0].student_id == 1
    assert results[0].attendance_date == "2026-08-30"

    connection.close()


def test_attendance_service_lists_empty_for_date_with_no_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL,
            remark TEXT
        )
        """
    )

    service = AttendanceService(
        AttendanceRepository(connection),
        tenant_id="school-001",
    )

    results = service.list_by_date("2026-08-30")

    assert results == []

    connection.close()



def test_attendance_service_allows_user_with_write_permission(tmp_path):
    import database
    from models.role import Role
    from models.permission import Permission
    from models.user_role import UserRoleLink
    from models.role_permission import RolePermissionLink
    from repositories.role_repository import RoleRepository
    from repositories.permission_repository import PermissionRepository
    from repositories.user_role_repository import UserRoleRepository
    from repositories.role_permission_repository import RolePermissionRepository

    connection = database.get_connection()
    try:
        tenant_id = "school-auth-positive"

        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_id, "Teacher", "teacher-positive@test", "member", "active"),
        )
        user_id = cursor.lastrowid

        student_cursor = connection.execute(
            """
            INSERT INTO students
                (tenant_id, user_id, name, class_name, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                user_id,
                "Student One",
                "Primary",
                "active",
            ),
        )
        student_id = student_cursor.lastrowid

        role = RoleRepository(connection).create(
            Role(None, tenant_id, "teacher", "Teacher")
        )

        permission = PermissionRepository(connection).create(
            Permission(
                None,
                tenant_id,
                "attendance.write",
                "Record attendance",
            )
        )

        UserRoleRepository(connection).create(
            UserRoleLink(tenant_id, user_id, role.id)
        )

        RolePermissionRepository(connection).create(
            RolePermissionLink(
                tenant_id,
                role.id,
                permission.id,
            )
        )

        service = AttendanceService(
            repository=AttendanceRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            user_id=user_id,
        )

        result = service.record(
            Attendance(
                id=None,
                tenant_id=tenant_id,
                student_id=student_id,
                attendance_date="2026-08-31",
                status="present",
            )
        )

        assert result.id is not None
        assert result.tenant_id == tenant_id
        assert result.status == "present"

    finally:
        connection.close()

def test_attendance_service_requires_write_permission(tmp_path):
    import database
    from models.role import Role
    from models.permission import Permission
    from models.user_role import UserRoleLink
    from models.role_permission import RolePermissionLink
    from repositories.role_repository import RoleRepository
    from repositories.permission_repository import PermissionRepository
    from repositories.user_role_repository import UserRoleRepository
    from repositories.role_permission_repository import RolePermissionRepository

    connection = database.get_connection()
    try:
        tenant_id = "school-auth"
        cursor = connection.execute(
            """
            INSERT INTO users
                (tenant_id, name, email, role, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tenant_id, "Teacher", "teacher@test", "member", "active"),
        )
        user_id = cursor.lastrowid

        role = RoleRepository(connection).create(
            Role(None, tenant_id, "teacher", "Teacher")
        )

        permission = PermissionRepository(connection).create(
            Permission(None, tenant_id, "attendance.write", "Record attendance")
        )

        UserRoleRepository(connection).create(
            UserRoleLink(tenant_id, user_id, role.id)
        )

        service = AttendanceService(
            repository=AttendanceRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            user_id=user_id,
        )

        with pytest.raises(PermissionError, match="attendance.write"):
            service.record(
                Attendance(
                    id=None,
                    tenant_id=tenant_id,
                    student_id=1,
                    attendance_date="2026-08-31",
                    status="present",
                )
            )
    finally:
        connection.close()
