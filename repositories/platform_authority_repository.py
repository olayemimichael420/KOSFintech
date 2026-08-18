from typing import Optional

from models.platform_authority import (
    PlatformAuthority,
    PlatformAuthorityRole,
)


class PlatformAuthorityRepository:
    """Repository for platform-level authority assignments."""

    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        authority: PlatformAuthority,
    ) -> PlatformAuthority:
        cursor = self.connection.execute(
            """
            INSERT INTO platform_authorities (
                user_id,
                role,
                status,
                transferred_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                authority.user_id,
                authority.role.value,
                authority.status,
                authority.transferred_at,
            ),
        )

        self.connection.commit()

        return self.get(cursor.lastrowid)

    def get(
        self,
        authority_id: int,
    ) -> Optional[PlatformAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                role,
                status,
                created_at,
                transferred_at
            FROM platform_authorities
            WHERE id = ?
            """,
            (authority_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def get_active_super_admin(
        self,
    ) -> Optional[PlatformAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                role,
                status,
                created_at,
                transferred_at
            FROM platform_authorities
            WHERE role = 'super_admin'
              AND status = 'active'
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def get_active_by_user(
        self,
        user_id: int,
    ) -> Optional[PlatformAuthority]:
        row = self.connection.execute(
            """
            SELECT
                id,
                user_id,
                role,
                status,
                created_at,
                transferred_at
            FROM platform_authorities
            WHERE user_id = ?
              AND role = 'super_admin'
              AND status = 'active'
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def deactivate(
        self,
        authority_id: int,
        transferred_at: Optional[str] = None,
    ) -> Optional[PlatformAuthority]:
        self.connection.execute(
            """
            UPDATE platform_authorities
            SET
                status = 'inactive',
                transferred_at = ?
            WHERE id = ?
              AND status = 'active'
            """,
            (
                transferred_at,
                authority_id,
            ),
        )

        self.connection.commit()

        return self.get(authority_id)

    @staticmethod
    def _to_model(row) -> PlatformAuthority:
        return PlatformAuthority(
            id=row["id"],
            user_id=row["user_id"],
            role=PlatformAuthorityRole(row["role"]),
            status=row["status"],
            created_at=row["created_at"],
            transferred_at=row["transferred_at"],
        )
