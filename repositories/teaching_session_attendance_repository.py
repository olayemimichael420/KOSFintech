from models.teaching_session_attendance import TeachingSessionAttendance


class TeachingSessionAttendanceRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        attendance: TeachingSessionAttendance,
    ) -> TeachingSessionAttendance:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_session_attendance (
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                attendance.tenant_id,
                attendance.teaching_session_id,
                attendance.membership_id,
                attendance.attendance_date,
                attendance.status,
                attendance.remark,
            ),
        )
        self.connection.commit()

        return TeachingSessionAttendance(
            id=cursor.lastrowid,
            tenant_id=attendance.tenant_id,
            teaching_session_id=attendance.teaching_session_id,
            membership_id=attendance.membership_id,
            attendance_date=attendance.attendance_date,
            status=attendance.status,
            remark=attendance.remark,
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            FROM teaching_session_attendance
            WHERE tenant_id = ?
            ORDER BY attendance_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeachingSessionAttendance(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                membership_id=row["membership_id"],
                attendance_date=row["attendance_date"],
                status=row["status"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def list_by_session(self, tenant_id: str, teaching_session_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            FROM teaching_session_attendance
            WHERE tenant_id = ?
              AND teaching_session_id = ?
            ORDER BY attendance_date, membership_id, id
            """,
            (tenant_id, teaching_session_id),
        ).fetchall()

        return [
            TeachingSessionAttendance(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                membership_id=row["membership_id"],
                attendance_date=row["attendance_date"],
                status=row["status"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def list_by_member(self, tenant_id: str, membership_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            FROM teaching_session_attendance
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY attendance_date, teaching_session_id, id
            """,
            (tenant_id, membership_id),
        ).fetchall()

        return [
            TeachingSessionAttendance(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                membership_id=row["membership_id"],
                attendance_date=row["attendance_date"],
                status=row["status"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def list_by_date(self, tenant_id: str, attendance_date: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            FROM teaching_session_attendance
            WHERE tenant_id = ?
              AND attendance_date = ?
            ORDER BY teaching_session_id, membership_id, id
            """,
            (tenant_id, attendance_date),
        ).fetchall()

        return [
            TeachingSessionAttendance(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                membership_id=row["membership_id"],
                attendance_date=row["attendance_date"],
                status=row["status"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def get(self, tenant_id: str, attendance_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                membership_id,
                attendance_date,
                status,
                remark
            FROM teaching_session_attendance
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, attendance_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingSessionAttendance(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_session_id=row["teaching_session_id"],
            membership_id=row["membership_id"],
            attendance_date=row["attendance_date"],
            status=row["status"],
            remark=row["remark"],
        )
