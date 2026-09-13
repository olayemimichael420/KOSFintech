from models.academic_subject import AcademicSubject


class AcademicSubjectRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, subject: AcademicSubject) -> AcademicSubject:
        cursor = self.connection.execute(
            """
            INSERT INTO academic_subjects (
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
        subject.id = cursor.lastrowid
        return subject

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                status
            FROM academic_subjects
            WHERE tenant_id = ?
            ORDER BY name
            """,
            (tenant_id,),
        ).fetchall()

        return [
            AcademicSubject(
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
            FROM academic_subjects
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, subject_id),
        ).fetchone()

        if row is None:
            return None

        return AcademicSubject(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            status=row["status"],
        )
