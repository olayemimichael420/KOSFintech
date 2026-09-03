import pytest

from models.parent_student import ParentStudentLink
from repositories.parent_student_repository import ParentStudentRepository
from services.parent_student_service import ParentStudentService


def test_parent_student_service_creates_link_for_bound_tenant(db_connection):
    db_connection.execute("INSERT INTO parents (tenant_id, name) VALUES (?, ?)", ("school-001", "Parent One"))
    parent_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_connection.execute("INSERT INTO students (tenant_id, name, class_name) VALUES (?, ?, ?)", ("school-001", "Student One", "Class 1"))
    student_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_connection.commit()
    repository = ParentStudentRepository(db_connection)
    service = ParentStudentService(repository, tenant_id="school-001")

    link = ParentStudentLink(
        tenant_id="school-001",
        parent_id=parent_id,
        student_id=student_id,
    )

    created = service.create(link)

    assert created == link


def test_parent_student_service_rejects_cross_tenant_create(db_connection):
    repository = ParentStudentRepository(db_connection)
    service = ParentStudentService(repository, tenant_id="school-001")

    link = ParentStudentLink(
        tenant_id="school-002",
        parent_id=5001,
        student_id=1,
    )

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create(link)


def test_parent_student_service_get_is_bound_to_tenant(db_connection):
    repository = ParentStudentRepository(db_connection)
    db_connection.execute("INSERT INTO parents (tenant_id, name) VALUES (?, ?)", ("school-001", "Parent Three"))
    parent_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_connection.execute("INSERT INTO students (tenant_id, name, class_name) VALUES (?, ?, ?)", ("school-001", "Student Three", "Class 3"))
    student_id = db_connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_connection.commit()
    service = ParentStudentService(repository, tenant_id="school-001")

    link = ParentStudentLink(
        tenant_id="school-001",
        parent_id=parent_id,
        student_id=student_id,
    )
    repository.create(link)

    result = service.get(parent_id=parent_id, student_id=student_id)

    assert result == link
