from models.progress import Progress


class ProgressRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, progress: Progress) -> Progress:
        cursor = self.connection.execute(
            """
            INSERT INTO progresses (
                tenant_id,
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                remark,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                progress.tenant_id,
                progress.membership_id,
                progress.teaching_content_id,
                progress.progress_date,
                progress.description,
                progress.remark,
                progress.status,
            ),
        )
        self.connection.commit()

        return Progress(
            id=cursor.lastrowid,
            tenant_id=progress.tenant_id,
            membership_id=progress.membership_id,
            teaching_content_id=progress.teaching_content_id,
            progress_date=progress.progress_date,
            description=progress.description,
            remark=progress.remark,
            status=progress.status,
        )

    def get(self, tenant_id: str, progress_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                remark,
                status
            FROM progresses
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, progress_id),
        ).fetchone()

        if row is None:
            return None

        return Progress(
            id=row["id"],
            tenant_id=row["tenant_id"],
            membership_id=row["membership_id"],
            teaching_content_id=row["teaching_content_id"],
            progress_date=row["progress_date"],
            description=row["description"],
            remark=row["remark"],
            status=row["status"],
        )

    def list_by_tenant(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                remark,
                status
            FROM progresses
            WHERE tenant_id = ?
            ORDER BY progress_date, id
            """,
            (tenant_id,),
        ).fetchall()

        return [
            Progress(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                progress_date=row["progress_date"],
                description=row["description"],
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
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                remark,
                status
            FROM progresses
            WHERE tenant_id = ?
              AND membership_id = ?
            ORDER BY progress_date, id
            """,
            (tenant_id, membership_id),
        ).fetchall()

        return [
            Progress(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                progress_date=row["progress_date"],
                description=row["description"],
                remark=row["remark"],
                status=row["status"],
            )
            for row in rows
        ]

    def list_by_content(self, tenant_id: str, teaching_content_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                membership_id,
                teaching_content_id,
                progress_date,
                description,
                remark,
                status
            FROM progresses
            WHERE tenant_id = ?
              AND teaching_content_id = ?
            ORDER BY progress_date, id
            """,
            (tenant_id, teaching_content_id),
        ).fetchall()

        return [
            Progress(
                id=row["id"],
                tenant_id=row["tenant_id"],
                membership_id=row["membership_id"],
                teaching_content_id=row["teaching_content_id"],
                progress_date=row["progress_date"],
                description=row["description"],
                remark=row["remark"],
                status=row["status"],
            )
            for row in rows
        ]
