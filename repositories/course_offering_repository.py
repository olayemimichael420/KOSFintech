from models.course_offering import CourseOffering


class CourseOfferingRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, offering: CourseOffering) -> CourseOffering:
        cursor = self.connection.execute(
            """
            INSERT INTO course_offerings (
                tenant_id,
                academic_class_id,
                academic_subject_id,
                academic_session_id,
                academic_term_id,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                offering.tenant_id,
                offering.academic_class_id,
                offering.academic_subject_id,
                offering.academic_session_id,
                offering.academic_term_id,
                offering.status,
            ),
        )
        self.connection.commit()

        return CourseOffering(
            id=cursor.lastrowid,
            tenant_id=offering.tenant_id,
            academic_class_id=offering.academic_class_id,
            academic_subject_id=offering.academic_subject_id,
            academic_session_id=offering.academic_session_id,
            academic_term_id=offering.academic_term_id,
            status=offering.status,
        )

    def get(self, tenant_id: str, offering_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                academic_class_id,
                academic_subject_id,
                academic_session_id,
                academic_term_id,
                status
            FROM course_offerings
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, offering_id),
        ).fetchone()

        if row is None:
            return None

        return CourseOffering(
            id=row["id"],
            tenant_id=row["tenant_id"],
            academic_class_id=row["academic_class_id"],
            academic_subject_id=row["academic_subject_id"],
            academic_session_id=row["academic_session_id"],
            academic_term_id=row["academic_term_id"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                academic_class_id,
                academic_subject_id,
                academic_session_id,
                academic_term_id,
                status
            FROM course_offerings
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            CourseOffering(
                id=row["id"],
                tenant_id=row["tenant_id"],
                academic_class_id=row["academic_class_id"],
                academic_subject_id=row["academic_subject_id"],
                academic_session_id=row["academic_session_id"],
                academic_term_id=row["academic_term_id"],
                status=row["status"],
            )
            for row in rows
        ]
