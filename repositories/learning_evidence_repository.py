from models.learning_evidence import LearningEvidence


class LearningEvidenceRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, evidence: LearningEvidence) -> LearningEvidence:
        cursor = self.connection.execute(
            """
            INSERT INTO learning_evidence (
                tenant_id,
                membership_id,
                teaching_content_id,
                evidence_date,
                description,
                remark
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                evidence.tenant_id,
                evidence.membership_id,
                evidence.teaching_content_id,
                evidence.evidence_date,
                evidence.description,
                evidence.remark,
            ),
        )
        self.connection.commit()

        return LearningEvidence(
            id=cursor.lastrowid,
            tenant_id=evidence.tenant_id,
            membership_id=evidence.membership_id,
            teaching_content_id=evidence.teaching_content_id,
            evidence_date=evidence.evidence_date,
            description=evidence.description,
            remark=evidence.remark,
        )

    def get(self, tenant_id: str, evidence_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                membership_id,
                teaching_content_id,
                evidence_date,
                description,
                remark
            FROM learning_evidence
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, evidence_id),
        ).fetchone()

        if row is None:
            return None

        return LearningEvidence(
            id=row["id"],
            tenant_id=row["tenant_id"],
            membership_id=row["membership_id"],
            teaching_content_id=row["teaching_content_id"],
            evidence_date=row["evidence_date"],
            description=row["description"],
            remark=row["remark"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                membership_id,
                teaching_content_id,
                evidence_date,
                description,
                remark
            FROM learning_evidence
            WHERE tenant_id = ?
            ORDER BY evidence_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            LearningEvidence(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                evidence_date=row["evidence_date"],
                description=row["description"],
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
                membership_id,
                teaching_content_id,
                evidence_date,
                description,
                remark
            FROM learning_evidence
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY evidence_date, teaching_content_id, id
            """,
            (tenant_id, membership_id),
        ).fetchall()

        return [
            LearningEvidence(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                evidence_date=row["evidence_date"],
                description=row["description"],
                remark=row["remark"],
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
                membership_id,
                teaching_content_id,
                evidence_date,
                description,
                remark
            FROM learning_evidence
            WHERE tenant_id = ?
              AND teaching_content_id = ?
            ORDER BY evidence_date, membership_id, id
            """,
            (tenant_id, teaching_content_id),
        ).fetchall()

        return [
            LearningEvidence(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                evidence_date=row["evidence_date"],
                description=row["description"],
                remark=row["remark"],
            )
            for row in rows
        ]
