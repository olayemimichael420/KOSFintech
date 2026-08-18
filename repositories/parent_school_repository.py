from models.parent_school import ParentSchoolLink


class ParentSchoolRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: ParentSchoolLink) -> ParentSchoolLink:
        self.connection.execute(
            """
            INSERT INTO parent_schools (
                tenant_id,
                parent_id
            )
            VALUES (?, ?)
            """,
            (
                link.tenant_id,
                link.parent_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, tenant_id: str, parent_id: int):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                parent_id
            FROM parent_schools
            WHERE tenant_id = ?
              AND parent_id = ?
            """,
            (tenant_id, parent_id),
        ).fetchone()

        if row is None:
            return None

        return ParentSchoolLink(
            tenant_id=row["tenant_id"],
            parent_id=row["parent_id"],
        )
