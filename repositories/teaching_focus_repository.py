from models.teaching_focus import TeachingFocus


class TeachingFocusRepository:
    def __init__(self, connection):
        self.connection = connection

    def series_exists(
        self,
        tenant_id: str,
        teaching_series_id: int,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM teaching_series
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, teaching_series_id),
        ).fetchone()

        return row is not None

    def create(self, focus: TeachingFocus) -> TeachingFocus:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_focuses (
                tenant_id,
                teaching_series_id,
                name,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                focus.tenant_id,
                focus.teaching_series_id,
                focus.name,
                focus.start_date,
                focus.end_date,
                focus.status,
            ),
        )
        self.connection.commit()

        return TeachingFocus(
            id=cursor.lastrowid,
            tenant_id=focus.tenant_id,
            teaching_series_id=focus.teaching_series_id,
            name=focus.name,
            start_date=focus.start_date,
            end_date=focus.end_date,
            status=focus.status,
        )

    def get(self, tenant_id: str, focus_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_series_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_focuses
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, focus_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingFocus(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_series_id=row["teaching_series_id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
        )

    def list(
        self,
        tenant_id: str,
        teaching_series_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_series_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_focuses
            WHERE tenant_id = ?
              AND teaching_series_id = ?
            ORDER BY start_date, id
            """,
            (tenant_id, teaching_series_id),
        ).fetchall()

        return [
            TeachingFocus(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_series_id=row["teaching_series_id"],
                name=row["name"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                status=row["status"],
            )
            for row in rows
        ]
