from models.parent import Parent


class ParentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, parent: Parent) -> Parent:
        cursor = self.connection.execute(
            """
            INSERT INTO parents (
                tenant_id,
                user_id,
                name,
                phone,
                email,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                parent.tenant_id,
                parent.user_id,
                parent.name,
                parent.phone,
                parent.email,
                parent.status,
            ),
        )

        self.connection.commit()
        parent.id = cursor.lastrowid

        return parent

    def get(self, tenant_id: str, parent_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                name,
                phone,
                email,
                status
            FROM parents
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, parent_id),
        ).fetchone()

        if row is None:
            return None

        return Parent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            name=row["name"],
            phone=row["phone"],
            email=row["email"],
            status=row["status"],
        )
