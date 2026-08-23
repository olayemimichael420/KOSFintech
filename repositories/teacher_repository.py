from models.teacher import Teacher


class TeacherRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, teacher: Teacher) -> Teacher:
        cursor = self.connection.execute(
            """
            INSERT INTO teachers (
                tenant_id,
                user_id,
                name,
                subject,
                qualification,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                teacher.tenant_id,
                teacher.user_id,
                teacher.name,
                teacher.subject,
                teacher.qualification,
                teacher.status,
            ),
        )

        self.connection.commit()
        teacher.id = cursor.lastrowid
        return teacher

    def get(self, tenant_id: str, teacher_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                name,
                subject,
                qualification,
                status
            FROM teachers
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, teacher_id),
        ).fetchone()

        if row is None:
            return None

        return Teacher(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            name=row["name"],
            subject=row["subject"],
            qualification=row["qualification"],
            status=row["status"],
        )
