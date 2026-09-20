from models.teacher_preacher_member import TeacherPreacherMemberLink


class TeacherPreacherMemberRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(
        self,
        link: TeacherPreacherMemberLink,
    ) -> TeacherPreacherMemberLink:
        self.connection.execute(
            """
            INSERT INTO teacher_preacher_members (
                tenant_id,
                teacher_preacher_id,
                membership_id
            )
            VALUES (?, ?, ?)
            """,
            (
                link.tenant_id,
                link.teacher_preacher_id,
                link.membership_id,
            ),
        )
        self.connection.commit()
        return link

    def get(
        self,
        tenant_id: str,
        teacher_preacher_id: int,
        membership_id: int,
    ):
        row = self.connection.execute(
            """
            SELECT
                tenant_id,
                teacher_preacher_id,
                membership_id
            FROM teacher_preacher_members
            WHERE tenant_id = ?
              AND teacher_preacher_id = ?
              AND membership_id = ?
            """,
            (
                tenant_id,
                teacher_preacher_id,
                membership_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return TeacherPreacherMemberLink(
            tenant_id=row["tenant_id"],
            teacher_preacher_id=row["teacher_preacher_id"],
            membership_id=row["membership_id"],
        )
