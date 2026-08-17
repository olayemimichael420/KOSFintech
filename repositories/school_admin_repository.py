from models.school_admin import SchoolAdmin


class SchoolAdminRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, admin: SchoolAdmin) -> SchoolAdmin:
        cursor = self.connection.execute(
            """
            INSERT INTO school_admins (
                tenant_id,
                user_id,
                role,
                phone,
                email,
                verified,
                verification_code,
                code_expires
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                admin.tenant_id,
                admin.user_id,
                admin.role,
                admin.phone,
                admin.email,
                admin.verified,
                admin.verification_code,
                admin.code_expires,
            ),
        )

        self.connection.commit()

        admin.id = cursor.lastrowid
        return admin

    def get(self, admin_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                role,
                phone,
                email,
                verified,
                verification_code,
                code_expires,
                created_at
            FROM school_admins
            WHERE id = ?
            """,
            (admin_id,),
        ).fetchone()

        if row is None:
            return None

        return SchoolAdmin(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            role=row["role"],
            phone=row["phone"],
            email=row["email"],
            verified=bool(row["verified"]),
            verification_code=row["verification_code"],
            code_expires=row["code_expires"],
            created_at=row["created_at"],
        )

    def list_by_school(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                role,
                phone,
                email,
                verified,
                verification_code,
                code_expires,
                created_at
            FROM school_admins
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            SchoolAdmin(
                id=row["id"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                role=row["role"],
                phone=row["phone"],
                email=row["email"],
                verified=bool(row["verified"]),
                verification_code=row["verification_code"],
                code_expires=row["code_expires"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
