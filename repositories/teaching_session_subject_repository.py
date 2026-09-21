from models.teaching_session_subject import TeachingSessionSubject


class TeachingSessionSubjectRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        offering: TeachingSessionSubject,
    ) -> TeachingSessionSubject:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_session_subjects (
                tenant_id,
                teaching_session_id,
                teaching_subject_id,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                offering.tenant_id,
                offering.teaching_session_id,
                offering.teaching_subject_id,
                offering.status,
            ),
        )
        self.connection.commit()

        return TeachingSessionSubject(
            id=cursor.lastrowid,
            tenant_id=offering.tenant_id,
            teaching_session_id=offering.teaching_session_id,
            teaching_subject_id=offering.teaching_subject_id,
            status=offering.status,
        )

    def get(self, tenant_id: str, offering_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                teaching_subject_id,
                status
            FROM teaching_session_subjects
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, offering_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingSessionSubject(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_session_id=row["teaching_session_id"],
            teaching_subject_id=row["teaching_subject_id"],
            status=row["status"],
        )

    def list(
        self,
        tenant_id: str,
        teaching_session_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                teaching_subject_id,
                status
            FROM teaching_session_subjects
            WHERE tenant_id = ?
              AND teaching_session_id = ?
            ORDER BY id
            """,
            (tenant_id, teaching_session_id),
        ).fetchall()

        return [
            TeachingSessionSubject(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                teaching_subject_id=row["teaching_subject_id"],
                status=row["status"],
            )
            for row in rows
        ]
