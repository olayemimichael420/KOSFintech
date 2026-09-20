from typing import Optional

from models.teaching_content import TeachingContent


class TeachingContentRepository:
    def __init__(self, connection):
        self.connection = connection

    def focus_exists(
        self,
        tenant_id: str,
        teaching_focus_id: int,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM teaching_focuses
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, teaching_focus_id),
        ).fetchone()
        return row is not None

    def create(self, content: TeachingContent) -> TeachingContent:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_contents (
                tenant_id,
                teaching_focus_id,
                name,
                description,
                sequence,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                content.tenant_id,
                content.teaching_focus_id,
                content.name,
                content.description,
                content.sequence,
                content.status,
            ),
        )
        self.connection.commit()

        return TeachingContent(
            id=cursor.lastrowid,
            tenant_id=content.tenant_id,
            teaching_focus_id=content.teaching_focus_id,
            name=content.name,
            description=content.description,
            sequence=content.sequence,
            status=content.status,
        )

    def get(
        self,
        tenant_id: str,
        content_id: int,
    ) -> Optional[TeachingContent]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_focus_id,
                name,
                description,
                sequence,
                status
            FROM teaching_contents
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, content_id),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list(
        self,
        tenant_id: str,
        teaching_focus_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_focus_id,
                name,
                description,
                sequence,
                status
            FROM teaching_contents
            WHERE tenant_id = ?
              AND teaching_focus_id = ?
            ORDER BY
                sequence IS NULL,
                sequence,
                name,
                id
            """,
            (tenant_id, teaching_focus_id),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> TeachingContent:
        return TeachingContent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_focus_id=row["teaching_focus_id"],
            name=row["name"],
            description=row["description"],
            sequence=row["sequence"],
            status=row["status"],
        )
