from models.section_teacher_assignment import SectionTeacherAssignment


class SectionTeacherAssignmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        assignment: SectionTeacherAssignment,
    ) -> SectionTeacherAssignment:
        cursor = self.connection.execute(
            """
            INSERT INTO section_teacher_assignments (
                tenant_id,
                course_section_id,
                teacher_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                assignment.tenant_id,
                assignment.course_section_id,
                assignment.teacher_id,
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
                course_section_id,
                teacher_id,
                status
            FROM section_teacher_assignments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assignment_id),
        ).fetchone()

        if row is None:
            return None

        return SectionTeacherAssignment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            course_section_id=row["course_section_id"],
            teacher_id=row["teacher_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str, course_section_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                course_section_id,
                teacher_id,
                status
            FROM section_teacher_assignments
            WHERE tenant_id = ?
              AND course_section_id = ?
            ORDER BY id
            """,
            (tenant_id, course_section_id),
        ).fetchall()

        return [
            SectionTeacherAssignment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                course_section_id=row["course_section_id"],
                teacher_id=row["teacher_id"],
                status=row["status"],
            )
            for row in rows
        ]
