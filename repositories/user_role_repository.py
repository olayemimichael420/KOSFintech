from models.user_role import UserRoleLink


class UserRoleRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: UserRoleLink) -> UserRoleLink:
        self.connection.execute(
            """
            INSERT INTO user_roles (
                tenant_id,
                user_id,
                role_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.tenant_id,
                link.user_id,
                link.role_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, tenant_id: str, user_id: int, role_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                user_id,
                role_id
            FROM user_roles
            WHERE tenant_id = ?
              AND user_id = ?
              AND role_id = ?
            """,
            (tenant_id, user_id, role_id),
        ).fetchone()

        if row is None:
            return None

        return UserRoleLink(
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            role_id=row["role_id"],
        )
