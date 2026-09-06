import pytest

from models.school_student import SchoolStudentLink
from repositories.school_student_repository import SchoolStudentRepository
from services.school_student_service import SchoolStudentService


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
        VALUES ('school-001', 'school-student-test-role', 'Test role', 'active')
        """
    ).lastrowid

    permission_id = connection.execute(
        """
        INSERT INTO permissions (tenant_id, name, description, status)
        VALUES ('school-001', ?, 'Test permission', 'active')
        """,
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


def seed_student(connection):
    student_id = connection.execute(
        """
        INSERT INTO students (
            tenant_id, name, class_name, status
        )
        VALUES ('school-001', 'Student One', 'Class 1', 'active')
        """
    ).lastrowid

    connection.commit()
    return student_id


def test_school_student_service_authorized_read_succeeds(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "school_student.read",
    )
    student_id = seed_student(db_connection)

    repository = SchoolStudentRepository(db_connection)
    repository.create(
        SchoolStudentLink(
            tenant_id="school-001",
            student_id=student_id,
        )
    )

    service = SchoolStudentService(
        repository=repository,
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    result = service.get(student_id)

    assert result is not None
    assert result.student_id == student_id
    assert result.tenant_id == "school-001"


def test_school_student_service_unauthorized_read_fails(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "school_student.write",
    )
    student_id = seed_student(db_connection)

    repository = SchoolStudentRepository(db_connection)
    repository.create(
        SchoolStudentLink(
            tenant_id="school-001",
            student_id=student_id,
        )
    )

    service = SchoolStudentService(
        repository=repository,
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    with pytest.raises(
        PermissionError,
        match="school_student.read",
    ):
        service.get(student_id)


def test_school_student_service_authorized_write_succeeds(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "school_student.write",
    )
    student_id = seed_student(db_connection)

    service = SchoolStudentService(
        repository=SchoolStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = SchoolStudentLink(
        tenant_id="school-001",
        student_id=student_id,
    )

    created = service.create(link)

    assert created == link


def test_school_student_service_unauthorized_write_fails(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "school_student.read",
    )
    student_id = seed_student(db_connection)

    service = SchoolStudentService(
        repository=SchoolStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = SchoolStudentLink(
        tenant_id="school-001",
        student_id=student_id,
    )

    with pytest.raises(
        PermissionError,
        match="school_student.write",
    ):
        service.create(link)


def test_school_student_service_rejects_cross_tenant_write(db_connection):
    user_id = seed_user_with_permission(
        db_connection,
        "school_student.write",
    )
    student_id = seed_student(db_connection)

    service = SchoolStudentService(
        repository=SchoolStudentRepository(db_connection),
        tenant_id="school-001",
        connection=db_connection,
        user_id=user_id,
    )

    link = SchoolStudentLink(
        tenant_id="school-002",
        student_id=student_id,
    )

    with pytest.raises(
        ValueError,
        match="tenant mismatch",
    ):
        service.create(link)
