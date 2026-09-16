from typing import Optional

from models.tenant import Tenant


class TenantRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, tenant: Tenant) -> Tenant:
        cursor = self.connection.execute(
            """
            INSERT INTO tenants (
                tenant_id,
                status
            )
            VALUES (?, ?)
            """,
            (
                tenant.tenant_id,
                tenant.status,
            ),
        )

        self.connection.commit()

        return Tenant(
            id=cursor.lastrowid,
            tenant_id=tenant.tenant_id,
            status=tenant.status,
        )

    def get(
        self,
        tenant_id: str,
        tenant_pk: int,
    ) -> Optional[Tenant]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                status
            FROM tenants
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, tenant_pk),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def get_by_tenant_id(self, tenant_id: str) -> Optional[Tenant]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                status
            FROM tenants
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list_active(self) -> list[Tenant]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                status
            FROM tenants
            WHERE status = 'active'
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Tenant:
        return Tenant(
            id=row["id"],
            tenant_id=row["tenant_id"],
            status=row["status"],
        )
