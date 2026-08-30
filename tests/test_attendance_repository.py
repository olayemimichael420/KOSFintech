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
