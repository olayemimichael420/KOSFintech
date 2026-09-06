import pytest

from models.teacher_student import TeacherStudentLink
from repositories.teacher_student_repository import TeacherStudentRepository
from services.teacher_student_service import TeacherStudentService


def seed_user_with_permission(connection, permission_name):
    user_id = connection.execute(
        """
        INSERT INTO users (tenant_id, name, role, status)
        VALUES ('school-001', 'Authorized User', 'member', 'active')
        """
    ).lastrowid

    role_id = connection.execute(
        """
        INSERT INTO roles (tenant_id, name, description, status)
        VALUES ('school-001', 'teacher-student-test-role', 'Test role', 'active')
        """
    ).lastrowid

    permission_id = connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, description, status)
        VALUES ('school-001', ?, 'Test permission', 'active')
        """
        ,
        (permission_name,),
    ).lastrowid

    connection.execute(
        """
        INSERT INTO user_roles (tenant_id, user_id, role_id)
        VALUES ('school-001', ?, ?)
        """,
        (user_id, role_id),
    )

    connection.execute(
        """
        INSERT INTO role_permissions (tenant_id, role_id, permission_id)
        VALUES ('school-001', ?, ?)
        """,
        (role_id, permission_id),
    )

    connection.commit()
    return user_id


def seed_teacher_and_student(connection):
    teacher_id = connection.execute(
        """
        INSERT INTO teachers (
            tenant_id, name, subject, status
        )
        VALUES ('school-001', 'Teacher One', 'Mathematics', 'active')
        """
    ).lastrowid

    student_id = connection.execute(
        """
        INSERT INTO students (
            tenant_id, name, class_name, status
        )
        VALUES ('school-001', 'Student One', 'Class 1', 'active')
        """
    ).lastrowid

    connection.commit()
    return teacher_id, student_id


def test_teacher_student_service_authorized_read_succeeds(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "teacher_student.read",
    )
    teacher_id, student_id = seed_teacher_and_student(db_connection)

    repository = TeacherStudentRepository(db_connection)
    repository.create(
        TeacherStudentLink(
            tenant_id="school-001",
            teacher_id=teacher_id,
            student_id=student_id,
        )
    )

    service = TeacherStudentService(
        repository=repository,
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    result = service.get(teacher_id, student_id)

    assert result is not None
    assert result.teacher_id == teacher_id
    assert result.student_id == student_id


def test_teacher_student_service_unauthorized_read_fails(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "teacher_student.write",
    )
    teacher_id, student_id = seed_teacher_and_student(db_connection)

    repository = TeacherStudentRepository(db_connection)
    repository.create(
        TeacherStudentLink(
            tenant_id="school-001",
            teacher_id=teacher_id,
            student_id=student_id,
        )
    )

    service = TeacherStudentService(
        repository=repository,
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="teacher_student.read",
    ):
        service.get(teacher_id, student_id)


def test_teacher_student_service_authorized_write_succeeds(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "teacher_student.write",
    )
    teacher_id, student_id = seed_teacher_and_student(db_connection)

    service = TeacherStudentService(
        repository=TeacherStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = TeacherStudentLink(
        tenant_id="school-001",
        teacher_id=teacher_id,
        student_id=student_id,
    )

    created = service.create(link)

    assert created == link


def test_teacher_student_service_unauthorized_write_fails(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "teacher_student.read",
    )
    teacher_id, student_id = seed_teacher_and_student(db_connection)

    service = TeacherStudentService(
        repository=TeacherStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = TeacherStudentLink(
        tenant_id="school-001",
        teacher_id=teacher_id,
        student_id=student_id,
    )

    with pytest.raises(
        PermissionError,
        match="teacher_student.write",
    ):
        service.create(link)


def test_teacher_student_service_rejects_cross_tenant_write(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "teacher_student.write",
    )
    teacher_id, student_id = seed_teacher_and_student(db_connection)

    service = TeacherStudentService(
        repository=TeacherStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = TeacherStudentLink(
        tenant_id="school-002",
        teacher_id=teacher_id,
        student_id=student_id,
    )

    with pytest.raises(
        ValueError,
        match="tenant mismatch",
    ):
        service.create(link)
