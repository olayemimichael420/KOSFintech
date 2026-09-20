from models.teacher_preacher_subject_assignment import TeacherPreacherSubjectAssignment


class TeacherPreacherSubjectAssignmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self, assignment: TeacherPreacherSubjectAssignment
    ) -> TeacherPreacherSubjectAssignment:
        cursor = self.connection.execute(
            """
            INSERT INTO teacher_preacher_subject_assignments (
                tenant_id,
                teacher_preacher_id,
                teaching_subject_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                assignment.tenant_id,
                assignment.teacher_preacher_id,
                assignment.teaching_subject_id,
                assignment.status,
            ),
        )
        self.connection.commit()

        return TeacherPreacherSubjectAssignment(
            id=cursor.lastrowid,
            tenant_id=assignment.tenant_id,
            teacher_preacher_id=assignment.teacher_preacher_id,
            teaching_subject_id=assignment.teaching_subject_id,
            status=assignment.status,
        )

    def get(self, tenant_id: str, assignment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_preacher_id,
                teaching_subject_id,
                status
            FROM teacher_preacher_subject_assignments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assignment_id),
        ).fetchone()

        if row is None:
            return None

        return TeacherPreacherSubjectAssignment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teacher_preacher_id=row["teacher_preacher_id"],
            teaching_subject_id=row["teaching_subject_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_preacher_id,
                teaching_subject_id,
                status
            FROM teacher_preacher_subject_assignments
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeacherPreacherSubjectAssignment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teacher_preacher_id=row["teacher_preacher_id"],
                teaching_subject_id=row["teaching_subject_id"],
                status=row["status"],
            )
            for row in rows
        ]
