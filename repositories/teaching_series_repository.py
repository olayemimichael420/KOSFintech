from models.teaching_series import TeachingSeries


class TeachingSeriesRepository:
    def __init__(self, connection):
        self.connection = connection

    def session_exists(
        self,
        tenant_id: str,
        teaching_session_id: int,
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM teaching_sessions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, teaching_session_id),
        ).fetchone()

        return row is not None

    def create(self, series: TeachingSeries) -> TeachingSeries:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_series (
                tenant_id,
                teaching_session_id,
                name,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                series.tenant_id,
                series.teaching_session_id,
                series.name,
                series.start_date,
                series.end_date,
                series.status,
            ),
        )
        self.connection.commit()

        return TeachingSeries(
            id=cursor.lastrowid,
            tenant_id=series.tenant_id,
            teaching_session_id=series.teaching_session_id,
            name=series.name,
            start_date=series.start_date,
            end_date=series.end_date,
            status=series.status,
        )

    def get(self, tenant_id: str, series_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_series
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, series_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingSeries(
            id=row["id"],
            tenant_id=row["tenant_id"],
            teaching_session_id=row["teaching_session_id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
        )

    def list(
        self,
        tenant_id: str,
        teaching_session_id: int,
    ):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                teaching_session_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_series
            WHERE tenant_id = ?
              AND teaching_session_id = ?
            ORDER BY start_date, id
            """,
            (tenant_id, teaching_session_id),
        ).fetchall()

        return [
            TeachingSeries(
                id=row["id"],
                tenant_id=row["tenant_id"],
                teaching_session_id=row["teaching_session_id"],
                name=row["name"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                status=row["status"],
            )
            for row in rows
        ]
