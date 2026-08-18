from typing import Optional

from models.administration import Administration


class AdministrationRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, administration: Administration) -> Administration:
        cursor = self.connection.execute(
            """
            INSERT INTO administrations (
                tenant_id,
                name,
                administration_type,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                administration.tenant_id,
                administration.name,
                administration.administration_type,
                administration.status,
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                administration_type,
                status,
                created_at
            FROM administrations
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return self._to_model(row)

    def get_by_id(self, administration_id: int) -> Optional[Administration]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                administration_type,
                status,
                created_at
            FROM administrations
            WHERE id = ?
            """,
            (administration_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def get_by_tenant_id(
        self,
        tenant_id: str,
    ) -> Optional[Administration]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                administration_type,
                status,
                created_at
            FROM administrations
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_active(self) -> list[Administration]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                administration_type,
                status,
                created_at
            FROM administrations
            WHERE status = 'active'
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Administration:
        return Administration(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            administration_type=row["administration_type"],
            status=row["status"],
            created_at=row["created_at"],
        )
