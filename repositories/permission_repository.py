from models.permission import Permission


class PermissionRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, permission: Permission) -> Permission:
        cursor = self.connection.execute(
            """
            INSERT INTO permissions (
                tenant_id,
                name,
                description,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                permission.tenant_id,
                permission.name,
                permission.description,
                permission.status,
            ),
        )

        self.connection.commit()

        permission.id = cursor.lastrowid
        return permission

    def get(self, tenant_id: str, permission_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                status
            FROM permissions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, permission_id),
        ).fetchone()

        if row is None:
            return None

        return Permission(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
        )
