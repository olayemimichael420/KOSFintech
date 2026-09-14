from models.section_student_enrollment import SectionStudentEnrollment


class SectionStudentEnrollmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        enrollment: SectionStudentEnrollment,
    ) -> SectionStudentEnrollment:
        cursor = self.connection.execute(
            """
            INSERT INTO section_student_enrollments (
                tenant_id,
                course_section_id,
                student_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                enrollment.tenant_id,
                enrollment.course_section_id,
                enrollment.student_id,
                enrollment.status,
            ),
        )
        self.connection.commit()

        enrollment.id = cursor.lastrowid
        return enrollment

    def get(self, tenant_id: str, enrollment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                course_section_id,
                student_id,
                status
            FROM section_student_enrollments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, enrollment_id),
        ).fetchone()

        if row is None:
            return None

        return SectionStudentEnrollment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            course_section_id=row["course_section_id"],
            student_id=row["student_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str, course_section_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                course_section_id,
                student_id,
                status
            FROM section_student_enrollments
            WHERE tenant_id = ?
              AND course_section_id = ?
            ORDER BY id
            """,
            (tenant_id, course_section_id),
        ).fetchall()

        return [
            SectionStudentEnrollment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                course_section_id=row["course_section_id"],
                student_id=row["student_id"],
                status=row["status"],
            )
            for row in rows
        ]
