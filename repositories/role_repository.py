from models.role import Role


class RoleRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, role: Role) -> Role:
        cursor = self.connection.execute(
            """
            INSERT INTO roles (
                tenant_id,
                name,
                description,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                role.tenant_id,
                role.name,
                role.description,
                role.status,
            ),
        )

        self.connection.commit()

        role.id = cursor.lastrowid
        return role

    def get(self, role_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                status
            FROM roles
            WHERE id = ?
            """,
            (role_id,),
        ).fetchone()

        if row is None:
            return None

        return Role(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
        )
