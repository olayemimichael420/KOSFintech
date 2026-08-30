import sqlite3

from models.attendance import Attendance
from repositories.attendance_repository import AttendanceRepository


def test_create_and_get_attendance():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    attendance = Attendance(
        id=None,
        tenant_id="school-001",
        student_id=1,
        attendance_date="2026-08-29",
    )

    created = repository.create(attendance)

    assert created.id is not None

    result = repository.get("school-001", created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.student_id == 1
    assert result.attendance_date == "2026-08-29"
    assert result.status == "present"

    connection.close()


def test_list_by_tenant_returns_only_that_tenants_attendance():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
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
            attendance_date="2026-08-29",
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

    results = repository.list_by_tenant("school-001")

    assert len(results) == 2
    assert all(item.tenant_id == "school-001" for item in results)
    assert [item.attendance_date for item in results] == [
        "2026-08-29",
        "2026-08-30",
    ]

    connection.close()

def test_list_by_student_returns_only_that_students_attendance_within_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
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
            student_id=2,
            attendance_date="2026-08-29",
            status="absent",
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
            tenant_id="school-002",
            student_id=1,
            attendance_date="2026-08-28",
            status="excused",
        )
    )

    results = repository.list_by_student("school-001", 1)

    assert len(results) == 2
    assert all(item.tenant_id == "school-001" for item in results)
    assert all(item.student_id == 1 for item in results)
    assert [item.attendance_date for item in results] == [
        "2026-08-29",
        "2026-08-30",
    ]

    connection.close()


def test_list_by_student_returns_empty_for_student_with_no_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            remark TEXT
        )
        """
    )

    repository = AttendanceRepository(connection)

    results = repository.list_by_student("school-001", 999)

    assert results == []

    connection.close()
