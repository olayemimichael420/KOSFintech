from models.teaching_subject import TeachingSubject


class TeachingSubjectRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, subject: TeachingSubject) -> TeachingSubject:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_subjects (
                tenant_id,
                name,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                subject.tenant_id,
                subject.name,
                subject.status,
            ),
        )

        self.connection.commit()

        return TeachingSubject(
            id=cursor.lastrowid,
            tenant_id=subject.tenant_id,
            name=subject.name,
            status=subject.status,
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                status
            FROM teaching_subjects
            WHERE tenant_id = ?
            ORDER BY name
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeachingSubject(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                status=row["status"],
            )
            for row in rows
        ]

    def get(self, tenant_id: str, subject_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                status
            FROM teaching_subjects
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, subject_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingSubject(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            status=row["status"],
        )
