from models.teacher_subject_assignment import TeacherSubjectAssignment


class TeacherSubjectAssignmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        assignment: TeacherSubjectAssignment,
    ) -> TeacherSubjectAssignment:
        cursor = self.connection.execute(
            """
            INSERT INTO teacher_subject_assignments (
                tenant_id,
                teacher_id,
                academic_subject_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                assignment.tenant_id,
                assignment.teacher_id,
                assignment.academic_subject_id,
                assignment.status,
            ),
        )

        self.connection.commit()
        assignment.id = cursor.lastrowid
        return assignment

    def get(self, tenant_id: str, assignment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_id,
                academic_subject_id,
                status
            FROM teacher_subject_assignments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assignment_id),
        ).fetchone()

        if row is None:
            return None

        return TeacherSubjectAssignment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teacher_id=row["teacher_id"],
            academic_subject_id=row["academic_subject_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teacher_id,
                academic_subject_id,
                status
            FROM teacher_subject_assignments
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeacherSubjectAssignment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teacher_id=row["teacher_id"],
                academic_subject_id=row["academic_subject_id"],
                status=row["status"],
            )
            for row in rows
        ]
