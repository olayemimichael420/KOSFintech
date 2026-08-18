from models.school_student import SchoolStudentLink


class SchoolStudentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: SchoolStudentLink) -> SchoolStudentLink:
        self.connection.execute(
            """
            INSERT INTO school_students (
                tenant_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (
                link.tenant_id,
                link.student_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, tenant_id: str, student_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                student_id
            FROM school_students
            WHERE tenant_id = ?
              AND student_id = ?
            """,
            (tenant_id, student_id),
        ).fetchone()

        if row is None:
            return None

        return SchoolStudentLink(
            tenant_id=row["tenant_id"],
            student_id=row["student_id"],
        )
