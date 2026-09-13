from models.student_enrollment import StudentEnrollment


class StudentEnrollmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, enrollment: StudentEnrollment) -> StudentEnrollment:
        cursor = self.connection.execute(
            """
            INSERT INTO student_enrollments (
                tenant_id,
                student_id,
                academic_class_id,
                academic_session_id,
                academic_term_id,
                enrollment_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                enrollment.tenant_id,
                enrollment.student_id,
                enrollment.academic_class_id,
                enrollment.academic_session_id,
                enrollment.academic_term_id,
                enrollment.enrollment_date,
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
                student_id,
                academic_class_id,
                academic_session_id,
                academic_term_id,
                enrollment_date,
                status
            FROM student_enrollments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, enrollment_id),
        ).fetchone()

        if row is None:
            return None

        return StudentEnrollment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            student_id=row["student_id"],
            academic_class_id=row["academic_class_id"],
            academic_session_id=row["academic_session_id"],
            academic_term_id=row["academic_term_id"],
            enrollment_date=row["enrollment_date"],
            status=row["status"],
        )

    def list(self, tenant_id: str, student_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                student_id,
                academic_class_id,
                academic_session_id,
                academic_term_id,
                enrollment_date,
                status
            FROM student_enrollments
            WHERE tenant_id = ?
              AND student_id = ?
            ORDER BY
                enrollment_date,
                id
            """,
            (tenant_id, student_id),
        ).fetchall()

        return [
            StudentEnrollment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                student_id=row["student_id"],
                academic_class_id=row["academic_class_id"],
                academic_session_id=row["academic_session_id"],
                academic_term_id=row["academic_term_id"],
                enrollment_date=row["enrollment_date"],
                status=row["status"],
            )
            for row in rows
        ]
