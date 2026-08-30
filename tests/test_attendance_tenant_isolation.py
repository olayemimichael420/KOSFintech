import sqlite3

from models.attendance import Attendance
from repositories.attendance_repository import AttendanceRepository
from services.attendance_service import AttendanceService


def create_schema(connection):
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
    connection.commit()


def test_repository_cannot_read_attendance_from_another_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        repository = AttendanceRepository(connection)

        attendance = repository.create(
            Attendance(
                id=None,
                tenant_id="school-001",
                student_id=1,
                attendance_date="2026-08-29",
                status="present",
            )
        )

        assert repository.get(
            "school-001",
            attendance.id,
        ) is not None

        assert repository.get(
            "school-002",
            attendance.id,
        ) is None

    finally:
        connection.close()


def test_service_cannot_read_attendance_from_another_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

        repository = AttendanceRepository(connection)
        service = AttendanceService(repository, tenant_id="school-001")

        attendance = service.record(
            Attendance(
                id=None,
                tenant_id="school-001",
                student_id=1,
                attendance_date="2026-08-29",
                status="present",
            )
        )

        assert service.get(
            "school-001",
            attendance.id,
        ) is not None

        assert service.get(
            "school-002",
            attendance.id,
        ) is None

    finally:
        connection.close()


def test_two_tenants_can_have_independent_attendance_records():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        create_schema(connection)

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

        assert first.id != second.id

        assert repository.get(
            "school-001",
            first.id,
        ).tenant_id == "school-001"

        assert repository.get(
            "school-002",
            second.id,
        ).tenant_id == "school-002"

        assert repository.get(
            "school-001",
            second.id,
        ) is None

        assert repository.get(
            "school-002",
            first.id,
        ) is None

    finally:
        connection.close()
