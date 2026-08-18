from models.user_school import UserSchoolLink


class UserSchoolRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: UserSchoolLink) -> UserSchoolLink:
        self.connection.execute(
            """
            INSERT INTO user_schools (
                tenant_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                link.tenant_id,
                link.user_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, tenant_id: str, user_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                user_id
            FROM user_schools
            WHERE tenant_id = ?
              AND user_id = ?
            """,
            (tenant_id, user_id),
        ).fetchone()

        if row is None:
            return None

        return UserSchoolLink(
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )
