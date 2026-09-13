from models.academic_class import AcademicClass


class AcademicClassRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, academic_class: AcademicClass) -> AcademicClass:
        cursor = self.connection.execute(
            """
            INSERT INTO academic_classes (
                tenant_id,
                name,
                education_level,
                sequence,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                academic_class.tenant_id,
                academic_class.name,
                academic_class.education_level,
                academic_class.sequence,
                academic_class.status,
            ),
        )
        self.connection.commit()

        academic_class.id = cursor.lastrowid
        return academic_class

    def get(self, tenant_id: str, class_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                education_level,
                sequence,
                status
            FROM academic_classes
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, class_id),
        ).fetchone()

        if row is None:
            return None

        return AcademicClass(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            education_level=row["education_level"],
            sequence=row["sequence"],
            status=row["status"],
        )

    def list(self, tenant_id: str):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                name,
                education_level,
                sequence,
                status
            FROM academic_classes
            WHERE tenant_id = ?
            ORDER BY
                sequence IS NULL,
                sequence,
                name
            """,
            (tenant_id,),
        ).fetchall()

        return [
            AcademicClass(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                education_level=row["education_level"],
                sequence=row["sequence"],
                status=row["status"],
            )
            for row in rows
        ]
