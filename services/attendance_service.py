from models.attendance import Attendance


class AttendanceService:
    ALLOWED_STATUSES = {
        "present",
        "absent",
        "late",
        "excused",
    }

    def __init__(self, repository, tenant_id: str):
        self.repository = repository
        self.tenant_id = tenant_id

    def record(self, attendance: Attendance) -> Attendance:
        if attendance.status not in self.ALLOWED_STATUSES:
            raise ValueError("invalid attendance status")

        if attendance.tenant_id != self.tenant_id:
            raise ValueError("attendance tenant mismatch")

        return self.repository.create(attendance)

    def list(self):
        return self.repository.list_by_tenant(
            self.tenant_id,
        )

    def get(self, attendance_id: int):
        return self.repository.get(
            self.tenant_id,
            attendance_id,
        )
