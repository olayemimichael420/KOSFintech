from models.teacher_preacher import TeacherPreacher, TeacherPreacherRole


class TeacherPreacherRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, capacity: TeacherPreacher) -> TeacherPreacher:
        cursor = self.connection.execute(
            """
            INSERT INTO teacher_preachers (
                tenant_id,
                person_id,
                role,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                capacity.tenant_id,
                capacity.person_id,
                capacity.role.value,
                capacity.status,
            ),
        )
        self.connection.commit()

        return TeacherPreacher(
            id=cursor.lastrowid,
            tenant_id=capacity.tenant_id,
            person_id=capacity.person_id,
            role=capacity.role,
            status=capacity.status,
        )

    def get(self, tenant_id: str, teacher_preacher_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                person_id,
                role,
                status
            FROM teacher_preachers
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, teacher_preacher_id),
        ).fetchone()

        if row is None:
            return None

        return TeacherPreacher(
            id=row["id"],
            tenant_id=row["tenant_id"],
            person_id=row["person_id"],
            role=TeacherPreacherRole(row["role"]),
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                person_id,
                role,
                status
            FROM teacher_preachers
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeacherPreacher(
                id=row["id"],
                tenant_id=row["tenant_id"],
                person_id=row["person_id"],
                role=TeacherPreacherRole(row["role"]),
                status=row["status"],
            )
            for row in rows
        ]
