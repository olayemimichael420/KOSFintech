from models.assessment_score import AssessmentScore


class AssessmentScoreRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, assessment_score: AssessmentScore) -> AssessmentScore:
        cursor = self.connection.execute(
            """
            INSERT INTO assessment_scores (
                tenant_id,
                assessment_id,
                membership_id,
                score,
                scored_date,
                remark
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_score.tenant_id,
                assessment_score.assessment_id,
                assessment_score.membership_id,
                assessment_score.score,
                assessment_score.scored_date,
                assessment_score.remark,
            ),
        )
        self.connection.commit()

        return AssessmentScore(
            id=cursor.lastrowid,
            tenant_id=assessment_score.tenant_id,
            assessment_id=assessment_score.assessment_id,
            membership_id=assessment_score.membership_id,
            score=assessment_score.score,
            scored_date=assessment_score.scored_date,
            remark=assessment_score.remark,
        )

    def get(self, tenant_id: str, assessment_score_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                score,
                scored_date,
                remark
            FROM assessment_scores
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, assessment_score_id),
        ).fetchone()

        if row is None:
            return None

        return AssessmentScore(
            id=row["id"],
            tenant_id=row["tenant_id"],
            assessment_id=row["assessment_id"],
            membership_id=row["membership_id"],
            score=row["score"],
            scored_date=row["scored_date"],
            remark=row["remark"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                score,
                scored_date,
                remark
            FROM assessment_scores
            WHERE tenant_id = ?
            ORDER BY scored_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            AssessmentScore(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                score=row["score"],
                scored_date=row["scored_date"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def list_by_assessment(self, tenant_id: str, assessment_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                score,
                scored_date,
                remark
            FROM assessment_scores
            WHERE tenant_id = ?
              AND assessment_id = ?
            ORDER BY scored_date, id
            """,
            (tenant_id, assessment_id),
        ).fetchall()

        return [
            AssessmentScore(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                score=row["score"],
                scored_date=row["scored_date"],
                remark=row["remark"],
            )
            for row in rows
        ]

    def list_by_member(self, tenant_id: str, membership_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                score,
                scored_date,
                remark
            FROM assessment_scores
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY scored_date, id
            """,
            (tenant_id, membership_id),
        ).fetchall()

        return [
            AssessmentScore(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                score=row["score"],
                scored_date=row["scored_date"],
                remark=row["remark"],
            )
            for row in rows
        ]
