from models.student import Student


class StudentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, student: Student) -> Student:
        cursor = self.connection.execute(
            """
            INSERT INTO students (
                tenant_id,
                user_id,
                name,
                class_name,
                age,
                guardian_id,
                enrollment_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student.tenant_id,
                student.user_id,
                student.name,
                student.class_name,
                student.age,
                student.guardian_id,
                student.enrollment_date,
                student.status,
            ),
        )

        self.connection.commit()
        student.id = cursor.lastrowid
        return student

    def get(self, tenant_id: str, student_id: int):
        row = self.connection.execute(
            """
            SELECT
                id,
                tenant_id,
                user_id,
                name,
                class_name,
                age,
                guardian_id,
                enrollment_date,
                status
            FROM students
            WHERE tenant_id = ?
              AND id = ?
            """,
            (tenant_id, student_id),
        ).fetchone()

        if row is None:
            return None

        return Student(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            name=row["name"],
            class_name=row["class_name"],
            age=row["age"],
            guardian_id=row["guardian_id"],
            enrollment_date=row["enrollment_date"],
            status=row["status"],
        )
