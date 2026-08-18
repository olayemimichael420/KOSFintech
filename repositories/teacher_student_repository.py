from models.teacher_student import TeacherStudentLink


class TeacherStudentRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, link: TeacherStudentLink) -> TeacherStudentLink:
        self.connection.execute(
            """
            INSERT INTO teacher_students (
                teacher_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (
                link.teacher_id,
                link.student_id,
            ),
        )

        self.connection.commit()
        return link

    def get(self, teacher_id: int, student_id: int):
        row = self.connection.execute(
            """
            SELECT
                teacher_id,
                student_id
            FROM teacher_students
            WHERE teacher_id = ?
              AND student_id = ?
            """,
            (teacher_id, student_id),
        ).fetchone()

        if row is None:
            return None

        return TeacherStudentLink(
            teacher_id=row["teacher_id"],
            student_id=row["student_id"],
        )
