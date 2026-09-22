from models.church_activity_participation import ChurchActivityParticipation


class ChurchActivityParticipationRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        participation: ChurchActivityParticipation,
    ) -> ChurchActivityParticipation:
        self.connection.execute(
            """
            INSERT INTO church_activity_participations (
                tenant_id,
                church_activity_id,
                membership_id
            )
            VALUES (?, ?, ?)
            """,
            (
                participation.tenant_id,
                participation.church_activity_id,
                participation.membership_id,
            ),
        )
        self.connection.commit()
        return participation

    def get(
        self,
        tenant_id: str,
        church_activity_id: int,
        membership_id: int,
    ):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                church_activity_id,
                membership_id
            FROM church_activity_participations
            WHERE tenant_id = ?
              AND church_activity_id = ?
              AND membership_id = ?
            """,
            (
                tenant_id,
                church_activity_id,
                membership_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return ChurchActivityParticipation(
            tenant_id=row["tenant_id"],
            church_activity_id=row["church_activity_id"],
            membership_id=row["membership_id"],
        )

    def list_by_activity(
        self,
        tenant_id: str,
        church_activity_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                tenant_id,
                church_activity_id,
                membership_id
            FROM church_activity_participations
            WHERE tenant_id = ?
              AND church_activity_id = ?
            ORDER BY membership_id
            """,
            (
                tenant_id,
                church_activity_id,
            ),
        ).fetchall()

        return [
            ChurchActivityParticipation(
                tenant_id=row["tenant_id"],
                church_activity_id=row["church_activity_id"],
                membership_id=row["membership_id"],
            )
            for row in rows
        ]

    def list_by_member(
        self,
        tenant_id: str,
        membership_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                tenant_id,
                church_activity_id,
                membership_id
            FROM church_activity_participations
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY church_activity_id
            """,
            (
                tenant_id,
                membership_id,
            ),
        ).fetchall()

        return [
            ChurchActivityParticipation(
                tenant_id=row["tenant_id"],
                church_activity_id=row["church_activity_id"],
                membership_id=row["membership_id"],
            )
            for row in rows
        ]
