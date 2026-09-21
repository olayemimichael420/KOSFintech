from models.teaching_content_teacher_preacher_assignment import (
    TeachingContentTeacherPreacherAssignment,
)


class TeachingContentTeacherPreacherAssignmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        assignment: TeachingContentTeacherPreacherAssignment,
    ) -> TeachingContentTeacherPreacherAssignment:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_content_teacher_preacher_assignments (
                tenant_id,
                teaching_content_id,
                teacher_preacher_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                assignment.tenant_id,
                assignment.teaching_content_id,
                assignment.teacher_preacher_id,
                assignment.status,
            ),
        )
        self.connection.commit()

        return TeachingContentTeacherPreacherAssignment(
            id=cursor.lastrowid,
            tenant_id=assignment.tenant_id,
            teaching_content_id=assignment.teaching_content_id,
            teacher_preacher_id=assignment.teacher_preacher_id,
            status=assignment.status,
        )

    def get(self, tenant_id: str, assignment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_content_id,
                teacher_preacher_id,
                status
            FROM teaching_content_teacher_preacher_assignments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assignment_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingContentTeacherPreacherAssignment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_content_id=row["teaching_content_id"],
            teacher_preacher_id=row["teacher_preacher_id"],
            status=row["status"],
        )

    def list(
        self,
        tenant_id: str,
        teaching_content_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_content_id,
                teacher_preacher_id,
                status
            FROM teaching_content_teacher_preacher_assignments
            WHERE tenant_id = ?
              AND teaching_content_id = ?
            ORDER BY id
            """,
            (tenant_id, teaching_content_id),
        ).fetchall()

        return [
            TeachingContentTeacherPreacherAssignment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_content_id=row["teaching_content_id"],
                teacher_preacher_id=row["teacher_preacher_id"],
                status=row["status"],
            )
            for row in rows
        ]
