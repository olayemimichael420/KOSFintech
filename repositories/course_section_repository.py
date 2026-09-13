from models.course_section import CourseSection


class CourseSectionRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, section: CourseSection) -> CourseSection:
        cursor = self.connection.execute(
            """
            INSERT INTO course_sections (
                tenant_id,
                course_offering_id,
                name,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                section.tenant_id,
                section.course_offering_id,
                section.name,
                section.status,
            ),
        )
        self.connection.commit()

        return CourseSection(
            id=cursor.lastrowid,
            tenant_id=section.tenant_id,
            course_offering_id=section.course_offering_id,
            name=section.name,
            status=section.status,
        )

    def get(self, tenant_id: str, section_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                course_offering_id,
                name,
                status
            FROM course_sections
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, section_id),
        ).fetchone()

        if row is None:
            return None

        return CourseSection(
            id=row["id"],
            tenant_id=row["tenant_id"],
            course_offering_id=row["course_offering_id"],
            name=row["name"],
            status=row["status"],
        )

    def list(self, tenant_id: str, course_offering_id: int):
        rows = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                course_offering_id,
                name,
                status
            FROM course_sections
            WHERE tenant_id = ?
              AND course_offering_id = ?
            ORDER BY id
            """,
            (tenant_id, course_offering_id),
        ).fetchall()

        return [
            CourseSection(
                id=row["id"],
                tenant_id=row["tenant_id"],
                course_offering_id=row["course_offering_id"],
                name=row["name"],
                status=row["status"],
            )
            for row in rows
        ]
