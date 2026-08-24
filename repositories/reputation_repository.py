from typing import Optional

from models.reputation import ReputationEvent


class ReputationRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, event: ReputationEvent) -> ReputationEvent:
        cursor = self.connection.execute(
            """
            INSERT INTO reputation_events (
                tenant_id,
                service_act_id,
                subject_user_id,
                reviewer_user_id,
                score,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.tenant_id,
                event.service_act_id,
                event.subject_user_id,
                event.reviewer_user_id,
                event.score,
                event.comment,
            ),
        )

        self.connection.commit()

        event.id = cursor.lastrowid

        return self.get(event.tenant_id, event.id)

    def get(
        self,
        tenant_id: str,
        event_id: int,
    ) -> Optional[ReputationEvent]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                subject_user_id,
                reviewer_user_id,
                score,
                comment,
                created_at
            FROM reputation_events
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, event_id),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_subject(
        self,
        tenant_id: str,
        subject_user_id: int,
    ) -> list[ReputationEvent]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                service_act_id,
                subject_user_id,
                reviewer_user_id,
                score,
                comment,
                created_at
            FROM reputation_events
            WHERE tenant_id = ?
              AND subject_user_id = ?
            ORDER BY id
            """,
            (tenant_id, subject_user_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def get_average_score(
        self,
        tenant_id: str,
        subject_user_id: int,
    ) -> float:
        row = self.connection.execute(
            """
            SELECT COALESCE(AVG(score), 0) AS average_score
            FROM reputation_events
            WHERE tenant_id = ?
              AND subject_user_id = ?
            """,
            (tenant_id, subject_user_id),
        ).fetchone()

        return float(row["average_score"])

    def exists_for_service_act(
        self,
        tenant_id: str,
        service_act_id: int,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM reputation_events
            WHERE tenant_id = ?
              AND service_act_id = ?
            LIMIT 1
            """,
            (tenant_id, service_act_id),
        ).fetchone()

        return row is not None

    @staticmethod
    def _to_model(row) -> ReputationEvent:
        return ReputationEvent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            service_act_id=row["service_act_id"],
            subject_user_id=row["subject_user_id"],
            reviewer_user_id=row["reviewer_user_id"],
            score=row["score"],
            comment=row["comment"],
            created_at=row["created_at"],
        )
