from models.grade import Grade


class GradeRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, grade: Grade) -> Grade:
        cursor = self.connection.execute(
            """
            INSERT INTO grades (
                tenant_id,
                name,
                description,
                minimum_score,
                maximum_score,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                grade.tenant_id,
                grade.name,
                grade.description,
                grade.minimum_score,
                grade.maximum_score,
                grade.status,
            ),
        )
        self.connection.commit()

        return Grade(
            id=cursor.lastrowid,
            tenant_id=grade.tenant_id,
            name=grade.name,
            description=grade.description,
            minimum_score=grade.minimum_score,
            maximum_score=grade.maximum_score,
            status=grade.status,
        )

    def get(self, tenant_id: str, grade_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                minimum_score,
                maximum_score,
                status
            FROM grades
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, grade_id),
        ).fetchone()

        if row is None:
            return None

        return Grade(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            minimum_score=row["minimum_score"],
            maximum_score=row["maximum_score"],
            status=row["status"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                minimum_score,
                maximum_score,
                status
            FROM grades
            WHERE tenant_id = ?
            ORDER BY minimum_score, maximum_score, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            Grade(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                description=row["description"],
                minimum_score=row["minimum_score"],
                maximum_score=row["maximum_score"],
                status=row["status"],
            )
            for row in rows
        ]
