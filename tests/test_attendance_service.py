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
