from models.school_teacher import SchoolTeacherLink


class SchoolTeacherRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: SchoolTeacherLink) -> SchoolTeacherLink:
        self.connection.execute(
            """
            INSERT INTO school_teachers (
                tenant_id,
                teacher_id
            )
            VALUES (?, ?)
            """,
            (
                link.tenant_id,
                link.teacher_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, tenant_id: str, teacher_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                teacher_id
            FROM school_teachers
            WHERE tenant_id = ?
              AND teacher_id = ?
            """,
            (tenant_id, teacher_id),
        ).fetchone()

        if row is None:
            return None

        return SchoolTeacherLink(
            tenant_id=row["tenant_id"],
            teacher_id=row["teacher_id"],
        )
