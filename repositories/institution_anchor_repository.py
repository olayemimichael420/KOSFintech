from typing import Optional

from models.institution_anchor import InstitutionAnchor


class InstitutionAnchorRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, anchor: InstitutionAnchor) -> InstitutionAnchor:
        cursor = self.connection.execute(
            """
            INSERT INTO institution_anchors (
                institution_type,
                name,
                provenance_reference,
                verification_status,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                anchor.institution_type,
                anchor.name,
                anchor.provenance_reference,
                anchor.verification_status,
                anchor.status,
            ),
        )

        self.connection.commit()

        return InstitutionAnchor(
            id=cursor.lastrowid,
            institution_type=anchor.institution_type,
            name=anchor.name,
            provenance_reference=anchor.provenance_reference,
            verification_status=anchor.verification_status,
            status=anchor.status,
            created_at=anchor.created_at,
        )

    def list_active(self) -> list[InstitutionAnchor]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                institution_type,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM institution_anchors
            WHERE status = 'active'
            ORDER BY id
            """
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> InstitutionAnchor:
        return InstitutionAnchor(
            id=row["id"],
            institution_type=row["institution_type"],
            name=row["name"],
            provenance_reference=row["provenance_reference"],
            verification_status=row["verification_status"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def get(self, anchor_id: int) -> Optional[InstitutionAnchor]:
        row = self.connection.execute(
            """
            SELECT
                id,
                institution_type,
                name,
                provenance_reference,
                verification_status,
                status,
                created_at
            FROM institution_anchors
            WHERE id = ?
            """,
            (anchor_id,),
        ).fetchone()

        if row is None:
            return None

        return InstitutionAnchor(
            id=row["id"],
            institution_type=row["institution_type"],
            name=row["name"],
            provenance_reference=row["provenance_reference"],
            verification_status=row["verification_status"],
            status=row["status"],
            created_at=row["created_at"],
        )
