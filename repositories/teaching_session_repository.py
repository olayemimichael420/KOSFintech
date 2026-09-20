from models.teaching_session import TeachingSession


class TeachingSessionRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, session: TeachingSession) -> TeachingSession:
        cursor = self.connection.execute(
            """
            INSERT INTO teaching_sessions (
                tenant_id,
                name,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.tenant_id,
                session.name,
                session.start_date,
                session.end_date,
                session.status,
            ),
        )
        self.connection.commit()

        return TeachingSession(
            id=cursor.lastrowid,
            tenant_id=session.tenant_id,
            name=session.name,
            start_date=session.start_date,
            end_date=session.end_date,
            status=session.status,
        )

    def get(self, tenant_id: str, session_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_sessions
            WHERE tenant_id = ? AND id = ?
            """,
            (tenant_id, session_id),
        ).fetchone()

        if row is None:
            return None

        return TeachingSession(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                start_date,
                end_date,
                status
            FROM teaching_sessions
            WHERE tenant_id = ?
            ORDER BY start_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            TeachingSession(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                status=row["status"],
            )
            for row in rows
        ]
