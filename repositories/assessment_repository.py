from models.assessment import Assessment


class AssessmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, assessment: Assessment) -> Assessment:
        cursor = self.connection.execute(
            """
            INSERT INTO assessments (
                tenant_id,
                teaching_content_id,
                name,
                description,
                assessment_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                assessment.tenant_id,
                assessment.teaching_content_id,
                assessment.name,
                assessment.description,
                assessment.assessment_date,
                assessment.status,
            ),
        )
        self.connection.commit()

        return Assessment(
            id=cursor.lastrowid,
            tenant_id=assessment.tenant_id,
            teaching_content_id=assessment.teaching_content_id,
            name=assessment.name,
            description=assessment.description,
            assessment_date=assessment.assessment_date,
            status=assessment.status,
        )

    def get(self, tenant_id: str, assessment_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_content_id,
                name,
                description,
                assessment_date,
                status
            FROM assessments
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assessment_id),
        ).fetchone()

        if row is None:
            return None

        return Assessment(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_content_id=row["teaching_content_id"],
            name=row["name"],
            description=row["description"],
            assessment_date=row["assessment_date"],
            status=row["status"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_content_id,
                name,
                description,
                assessment_date,
                status
            FROM assessments
            WHERE tenant_id = ?
            ORDER BY assessment_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            Assessment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_content_id=row["teaching_content_id"],
                name=row["name"],
                description=row["description"],
                assessment_date=row["assessment_date"],
                status=row["status"],
            )
            for row in rows
        ]

    def list_by_content(
        self,
        tenant_id: str,
        teaching_content_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_content_id,
                name,
                description,
                assessment_date,
                status
            FROM assessments
            WHERE tenant_id = ?
              AND teaching_content_id = ?
            ORDER BY assessment_date, id
            """,
            (tenant_id, teaching_content_id),
        ).fetchall()

        return [
            Assessment(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_content_id=row["teaching_content_id"],
                name=row["name"],
                description=row["description"],
                assessment_date=row["assessment_date"],
                status=row["status"],
            )
            for row in rows
        ]
