from typing import Optional

from models.administration_authority import (
    AdministrationAuthority,
    AdministrationAuthorityRole,
)


class AdministrationAuthorityRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        authority: AdministrationAuthority,
    ) -> AdministrationAuthority:
        cursor = self.connection.execute(
            """
            INSERT INTO administration_authorities (
                administration_id,
                user_id,
                role,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                authority.administration_id,
                authority.user_id,
                authority.role.value,
                authority.status,
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT
                id,
                administration_id,
                user_id,
                role,
                status,
                created_at
            FROM administration_authorities
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return self._to_model(row)

    def get(
        self,
        authority_id: int,
    ) -> Optional[AdministrationAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                administration_id,
                user_id,
                role,
                status,
                created_at
            FROM administration_authorities
            WHERE id = ?
            """,
            (authority_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def get_active_by_user_and_administration(
        self,
        user_id: int,
        administration_id: int,
    ) -> Optional[AdministrationAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                administration_id,
                user_id,
                role,
                status,
                created_at
            FROM administration_authorities
            WHERE user_id = ?
              AND administration_id = ?
              AND status = 'active'
            """,
            (
                user_id,
                administration_id,
            ),
        ).fetchone()

        return self._to_model(row) if row else None

    def get_active_by_administration_and_role(
        self,
        administration_id: int,
        role: AdministrationAuthorityRole,
    ) -> Optional[AdministrationAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                administration_id,
                user_id,
                role,
                status,
                created_at
            FROM administration_authorities
            WHERE administration_id = ?
              AND role = ?
              AND status = 'active'
            """,
            (
                administration_id,
                role.value,
            ),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_by_administration(
        self,
        administration_id: int,
    ) -> list[AdministrationAuthority]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                administration_id,
                user_id,
                role,
                status,
                created_at
            FROM administration_authorities
            WHERE administration_id = ?
            ORDER BY id
            """,
            (administration_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    def deactivate(self, authority_id: int) -> Optional[AdministrationAuthority]:
        self.connection.execute(
            """
            UPDATE administration_authorities
            SET status = 'inactive'
            WHERE id = ?
            """,
            (authority_id,),
        )

        self.connection.commit()

        return self.get(authority_id)

    @staticmethod
    def _to_model(row) -> AdministrationAuthority:
        return AdministrationAuthority(
            id=row["id"],
            administration_id=row["administration_id"],
            user_id=row["user_id"],
            role=AdministrationAuthorityRole(row["role"]),
            status=row["status"],
            created_at=row["created_at"],
        )
