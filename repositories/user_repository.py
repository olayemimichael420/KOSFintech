from models.user import User


class UserRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, user: User) -> User:
        cursor = self.connection.execute(
            """
            INSERT INTO users (
                tenant_id,
                name,
                email,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.tenant_id,
                user.name,
                user.email,
                user.role,
                user.status,
            ),
        )

        self.connection.commit()

        user.id = cursor.lastrowid
        return user

    def get(self, user_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                email,
                role,
                status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return User(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            email=row["email"],
            role=row["role"],
            status=row["status"],
        )
