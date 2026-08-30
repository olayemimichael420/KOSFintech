from models.attendance import Attendance


class AttendanceRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, attendance: Attendance) -> Attendance:
        cursor = self.connection.execute(
            """
            INSERT INTO attendance (
                tenant_id,
                student_id,
                attendance_date,
                status,
                remark
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                attendance.tenant_id,
                attendance.student_id,
                attendance.attendance_date,
                attendance.status,
                attendance.remark,
            ),
        )
        self.connection.commit()
        attendance.id = cursor.lastrowid
        return attendance

    def get(
        self,
        tenant_id: str,
        attendance_id: int,
    ):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                student_id,
                attendance_date,
                status,
                remark
            FROM attendance
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, attendance_id),
        ).fetchone()

        if row is None:
            return None

        return Attendance(
            id=row["id"],
            tenant_id=row["tenant_id"],
            student_id=row["student_id"],
            attendance_date=row["attendance_date"],
            status=row["status"],
            remark=row["remark"],
        )
