from typing import Optional

from models.service_binding import ServiceBinding


class ServiceBindingRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, binding: ServiceBinding) -> ServiceBinding:
        cursor = self.connection.execute(
            """
            INSERT INTO service_bindings (
                institution_anchor_id,
                tenant_id,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                binding.institution_anchor_id,
                binding.tenant_id,
                binding.status,
            ),
        )

        self.connection.commit()

        return ServiceBinding(
            id=cursor.lastrowid,
            institution_anchor_id=binding.institution_anchor_id,
            tenant_id=binding.tenant_id,
            status=binding.status,
            created_at=binding.created_at,
        )

    def get(self, binding_id: int) -> Optional[ServiceBinding]:
        row = self.connection.execute(
            """
            SELECT
                id,
                institution_anchor_id,
                tenant_id,
                status,
                created_at
            FROM service_bindings
            WHERE id = ?
            """,
            (binding_id,),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list_active(self) -> list[ServiceBinding]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                institution_anchor_id,
                tenant_id,
                status,
                created_at
            FROM service_bindings
            WHERE status = 'active'
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ServiceBinding:
        return ServiceBinding(
            id=row["id"],
            institution_anchor_id=row["institution_anchor_id"],
            tenant_id=row["tenant_id"],
            status=row["status"],
            created_at=row["created_at"],
        )
