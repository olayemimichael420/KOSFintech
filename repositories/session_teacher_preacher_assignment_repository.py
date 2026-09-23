from models.session_teacher_preacher_assignment import (
    SessionTeacherPreacherAssignment,
)


class SessionTeacherPreacherAssignmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        assignment: SessionTeacherPreacherAssignment,
    ) -> SessionTeacherPreacherAssignment:
        cursor = self.connection.execute(
            """
            INSERT INTO session_teacher_preacher_assignments (
                tenant_id,
                teacher_preacher_id,
                teaching_session_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                assignment.tenant_id,
                assignment.teacher_preacher_id,
                assignment.teaching_session_id,
                assignment.status,
            ),
        )
        self.connection.commit()

        return SessionTeacherPreacherAssignment(
            id=cursor.lastrowid,
            tenant_id=assignment.tenant_id,
            teacher_preacher_id=assignment.teacher_preacher_id,
            teaching_session_id=assignment.teaching_session_id,
            status=assignment.status,
        )

    def get(self, tenant_id: str, assignment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_preacher_id,
                teaching_session_id,
                status
            FROM session_teacher_preacher_assignments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assignment_id),
        ).fetchone()

        if row is None:
            return None

        return SessionTeacherPreacherAssignment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teacher_preacher_id=row["teacher_preacher_id"],
            teaching_session_id=row["teaching_session_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_preacher_id,
                teaching_session_id,
                status
            FROM session_teacher_preacher_assignments
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            SessionTeacherPreacherAssignment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teacher_preacher_id=row["teacher_preacher_id"],
                teaching_session_id=row["teaching_session_id"],
                status=row["status"],
            )
            for row in rows
        ]
