from typing import Optional

from models.person_user import PersonUserLink


class PersonUserRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: PersonUserLink) -> PersonUserLink:
        self.connection.execute(
            """
            INSERT INTO person_users (
                person_id,
                tenant_id,
                user_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.person_id,
                link.tenant_id,
                link.user_id,
            ),
        )
        self.connection.commit()
        return link

    def get_by_user(
        self,
        tenant_id: str,
        user_id: int,
    ) -> Optional[PersonUserLink]:
        row = self.connection.execute(
            """
            SELECT
                person_id,
                tenant_id,
                user_id
            FROM person_users
            WHERE tenant_id = ?
              AND user_id = ?
            """,
            (tenant_id, user_id),
        ).fetchone()

        if row is None:
            return None

        return PersonUserLink(
            person_id=row["person_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )

    def list_by_person(self, person_id: int) -> list[PersonUserLink]:
        rows = self.connection.execute(
            """
            SELECT
                person_id,
                tenant_id,
                user_id
            FROM person_users
            WHERE person_id = ?
            ORDER BY tenant_id, user_id
            """,
            (person_id,),
        ).fetchall()

        return [
            PersonUserLink(
                person_id=row["person_id"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
            )
            for row in rows
        ]
