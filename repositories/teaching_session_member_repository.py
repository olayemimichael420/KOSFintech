from models.teaching_session_member import TeachingSessionMemberLink


class TeachingSessionMemberRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        link: TeachingSessionMemberLink,
    ) -> TeachingSessionMemberLink:
        self.connection.execute(
            """
            INSERT INTO teaching_session_members (
                tenant_id,
                teaching_session_id,
                membership_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.tenant_id,
                link.teaching_session_id,
                link.membership_id,
            ),
        )
        self.connection.commit()
        return link

    def get(
        self,
        tenant_id: str,
        teaching_session_id: int,
        membership_id: int,
    ):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                teaching_session_id,
                membership_id
            FROM teaching_session_members
            WHERE tenant_id = ?
              AND teaching_session_id = ?
              AND membership_id = ?
            """,
            (
                tenant_id,
                teaching_session_id,
                membership_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return TeachingSessionMemberLink(
            tenant_id=row["tenant_id"],
            teaching_session_id=row["teaching_session_id"],
            membership_id=row["membership_id"],
        )
