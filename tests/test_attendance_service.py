import sqlite3

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

    service = AttendanceService(AttendanceRepository(connection))

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

    service = AttendanceService(AttendanceRepository(connection))

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
