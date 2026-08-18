from models.role_permission import RolePermissionLink


class RolePermissionRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: RolePermissionLink) -> RolePermissionLink:
        self.connection.execute(
            """
            INSERT INTO role_permissions (
                tenant_id,
                role_id,
                permission_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.tenant_id,
                link.role_id,
                link.permission_id,
            ),
        )

        self.connection.commit()
        return link

    def get(
        self,
        tenant_id: str,
        role_id: int,
        permission_id: int,
    ):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                role_id,
                permission_id
            FROM role_permissions
            WHERE tenant_id = ?
              AND role_id = ?
              AND permission_id = ?
            """,
            (tenant_id, role_id, permission_id),
        ).fetchone()

        if row is None:
            return None

        return RolePermissionLink(
            tenant_id=row["tenant_id"],
            role_id=row["role_id"],
            permission_id=row["permission_id"],
        )
