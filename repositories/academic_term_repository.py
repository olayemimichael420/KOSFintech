from models.academic_term import AcademicTerm


class AcademicTermRepository:
    def __init__(self, connection):
        self.connection = connection

    def session_exists(self, tenant_id: str, academic_session_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM academic_sessions
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, academic_session_id),
        ).fetchone()

        return row is not None

    def create(self, term: AcademicTerm) -> AcademicTerm:
        cursor = self.connection.execute(
            """
            INSERT INTO academic_terms (
                tenant_id,
                academic_session_id,
                name,
                start_date,
                end_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                term.tenant_id,
                term.academic_session_id,
                term.name,
                term.start_date,
                term.end_date,
                term.status,
            ),
        )
        self.connection.commit()
        term.id = cursor.lastrowid
        return term

    def get(self, tenant_id: str, term_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                academic_session_id,
                name,
                start_date,
                end_date,
                status
            FROM academic_terms
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, term_id),
        ).fetchone()

        if row is None:
            return None

        return AcademicTerm(
            id=row["id"],
            tenant_id=row["tenant_id"],
            academic_session_id=row["academic_session_id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
        )

    def list(self, tenant_id: str, academic_session_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                academic_session_id,
                name,
                start_date,
                end_date,
                status
            FROM academic_terms
            WHERE tenant_id = ?
              AND academic_session_id = ?
            ORDER BY start_date, id
            """,
            (tenant_id, academic_session_id),
        ).fetchall()

        return [
            AcademicTerm(
                id=row["id"],
                tenant_id=row["tenant_id"],
                academic_session_id=row["academic_session_id"],
                name=row["name"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                status=row["status"],
            )
            for row in rows
        ]
