from typing import Optional

from models.church_anchor import ChurchAnchor


class ChurchAnchorRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, anchor: ChurchAnchor) -> ChurchAnchor:
        cursor = self.connection.execute(
            """
            INSERT INTO church_anchors (
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                anchor.tenant_id,
                anchor.name,
                anchor.provenance_reference,
                anchor.verification_status,
                anchor.status,
            ),
        )

        self.connection.commit()

        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM church_anchors
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return self._to_model(row)

    def get_by_id(self, anchor_id: int) -> Optional[ChurchAnchor]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM church_anchors
            WHERE id = ?
            """,
            (anchor_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def get_by_tenant_id(
        self,
        tenant_id: str,
    ) -> Optional[ChurchAnchor]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM church_anchors
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        ).fetchone()

        return self._to_model(row) if row else None

    def list_active(self) -> list[ChurchAnchor]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM church_anchors
            WHERE status = 'active'
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ChurchAnchor:
        return ChurchAnchor(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            provenance_reference=row["provenance_reference"],
            verification_status=row["verification_status"],
            status=row["status"],
            created_at=row["created_at"],
        )
