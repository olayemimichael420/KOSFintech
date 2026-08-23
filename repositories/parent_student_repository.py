from models.parent_student import ParentStudentLink


class ParentStudentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: ParentStudentLink) -> ParentStudentLink:
        self.connection.execute(
            """
            INSERT INTO parent_students (
                tenant_id,
                parent_id,
                student_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.tenant_id,
                link.parent_id,
                link.student_id,
            ),
        )
        self.connection.commit()
        return link

    def get(self, tenant_id: str, parent_id: int, student_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                parent_id,
                student_id
            FROM parent_students
            WHERE tenant_id = ?
              AND parent_id = ?
              AND student_id = ?
            """,
            (tenant_id, parent_id, student_id),
        ).fetchone()

        if row is None:
            return None

        return ParentStudentLink(
            tenant_id=row["tenant_id"],
            parent_id=row["parent_id"],
            student_id=row["student_id"],
        )
