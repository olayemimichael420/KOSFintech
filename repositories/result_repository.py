from models.result import Result


class ResultRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, result: Result) -> Result:
        cursor = self.connection.execute(
            """
            INSERT INTO results (
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date,
                remark,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.tenant_id,
                result.assessment_id,
                result.membership_id,
                result.grade_id,
                result.result,
                result.result_date,
                result.remark,
                result.status,
            ),
        )
        self.connection.commit()

        return Result(
            id=cursor.lastrowid,
            tenant_id=result.tenant_id,
            assessment_id=result.assessment_id,
            membership_id=result.membership_id,
            grade_id=result.grade_id,
            result=result.result,
            result_date=result.result_date,
            remark=result.remark,
            status=result.status,
        )

    def get(self, tenant_id: str, result_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date,
                remark,
                status
            FROM results
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, result_id),
        ).fetchone()

        if row is None:
            return None

        return Result(
            id=row["id"],
            tenant_id=row["tenant_id"],
            assessment_id=row["assessment_id"],
            membership_id=row["membership_id"],
            grade_id=row["grade_id"],
            result=row["result"],
            result_date=row["result_date"],
            remark=row["remark"],
            status=row["status"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date,
                remark,
                status
            FROM results
            WHERE tenant_id = ?
            ORDER BY result_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            Result(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                grade_id=row["grade_id"],
                result=row["result"],
                result_date=row["result_date"],
                remark=row["remark"],
                status=row["status"],
            )
            for row in rows
        ]

    def list_by_assessment(self, tenant_id: str, assessment_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date,
                remark,
                status
            FROM results
            WHERE tenant_id = ?
              AND assessment_id = ?
            ORDER BY result_date, id
            """,
            (tenant_id, assessment_id),
        ).fetchall()

        return [
            Result(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                grade_id=row["grade_id"],
                result=row["result"],
                result_date=row["result_date"],
                remark=row["remark"],
                status=row["status"],
            )
            for row in rows
        ]

    def list_by_member(self, tenant_id: str, membership_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                assessment_id,
                membership_id,
                grade_id,
                result,
                result_date,
                remark,
                status
            FROM results
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY result_date, id
            """,
            (tenant_id, membership_id),
        ).fetchall()

        return [
            Result(
                id=row["id"],
                tenant_id=row["tenant_id"],
                assessment_id=row["assessment_id"],
                membership_id=row["membership_id"],
                grade_id=row["grade_id"],
                result=row["result"],
                result_date=row["result_date"],
                remark=row["remark"],
                status=row["status"],
            )
            for row in rows
        ]
