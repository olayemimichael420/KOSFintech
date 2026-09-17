from typing import Optional

from models.church_program import ChurchProgram


class ChurchProgramRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, program: ChurchProgram) -> ChurchProgram:
        cursor = self.connection.execute(
            """
            INSERT INTO church_programs (
                tenant_id,
                name,
                description,
                program_type,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                program.tenant_id,
                program.name,
                program.description,
                program.program_type,
                program.status,
            ),
        )
        self.connection.commit()
        return ChurchProgram(
            id=cursor.lastrowid,
            tenant_id=program.tenant_id,
            name=program.name,
            description=program.description,
            program_type=program.program_type,
            status=program.status,
        )

    def get(self, tenant_id: str, program_id: int) -> Optional[ChurchProgram]:
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                program_type,
                status
            FROM church_programs
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, program_id),
        ).fetchone()

        if row is None:
            return None

        return self._to_model(row)

    def list(self, tenant_id: str) -> list[ChurchProgram]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                description,
                program_type,
                status
            FROM church_programs
            WHERE tenant_id = ?
            ORDER BY id
            """,
            (tenant_id,),
        ).fetchall()

        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ChurchProgram:
        return ChurchProgram(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"],
            program_type=row["program_type"],
            status=row["status"],
        )
