from datetime import datetime
from typing import Optional

from models.membership import Membership


class MembershipRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, membership: Membership) -> Membership:
        cursor = self.connection.execute(
            """
            INSERT INTO memberships (
                tenant_id,
                person_id,
                church_anchor_id,
                membership_status,
                effective_from,
                effective_until,
                provenance_reference
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                membership.tenant_id,
                membership.person_id,
                membership.church_anchor_id,
                membership.membership_status,
                membership.effective_from,
                membership.effective_until,
                membership.provenance_reference,
            ),
        )
        self.connection.commit()

        return Membership(
            id=cursor.lastrowid,
            tenant_id=membership.tenant_id,
            person_id=membership.person_id,
            church_anchor_id=membership.church_anchor_id,
            membership_status=membership.membership_status,
            effective_from=membership.effective_from,
            effective_until=membership.effective_until,
            provenance_reference=membership.provenance_reference,
            created_at=membership.created_at,
        )

    def get(
        self,
        tenant_id: str,
        membership_id: int,
    ) -> Optional[Membership]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                person_id,
                church_anchor_id,
                membership_status,
                effective_from,
                effective_until,
                provenance_reference,
                created_at
            FROM memberships
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, membership_id),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list(self, tenant_id: str) -> list[Membership]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                person_id,
                church_anchor_id,
                membership_status,
                effective_from,
                effective_until,
                provenance_reference,
                created_at
            FROM memberships
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> Membership:
        def _parse_datetime(value):
            if value is None or isinstance(value, datetime):
                return value

            return datetime.fromisoformat(value)

        return Membership(
            id=row["id"],
            tenant_id=row["tenant_id"],
            person_id=row["person_id"],
            church_anchor_id=row["church_anchor_id"],
            membership_status=row["membership_status"],
            effective_from=_parse_datetime(row["effective_from"]),
            effective_until=_parse_datetime(row["effective_until"]),
            provenance_reference=row["provenance_reference"],
            created_at=row["created_at"],
        )
