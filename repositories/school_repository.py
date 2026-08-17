from models.school import School


class SchoolRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, school: School) -> School:
        self.connection.execute(
            """
            INSERT INTO schools (
                tenant_id,
                name,
                school_type,
                country,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                school.tenant_id,
                school.name,
                school.school_type,
                school.country,
                school.currency,
            ),
        )
        self.connection.commit()
        return school

    def get(self, tenant_id: str):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                name,
                school_type,
                country,
                currency,
                created_at
            FROM schools
            WHERE tenant_id = ?
            """,
            (tenant_id,),
        ).fetchone()

        if row is None:
            return None

        return School(
            tenant_id=row["tenant_id"],
            name=row["name"],
            school_type=row["school_type"],
            country=row["country"],
            currency=row["currency"],
            created_at=row["created_at"],
        )
