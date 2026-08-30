from models.attendance import Attendance


class AttendanceService:
    ALLOWED_STATUSES = {
        "present",
        "absent",
        "late",
        "excused",
    }

    def __init__(self, repository):
        self.repository = repository

    def record(self, attendance: Attendance) -> Attendance:
        if attendance.status not in self.ALLOWED_STATUSES:
            raise ValueError("invalid attendance status")

        return self.repository.create(attendance)

    def get(self, tenant_id: str, attendance_id: int):
        return self.repository.get(tenant_id, attendance_id)
