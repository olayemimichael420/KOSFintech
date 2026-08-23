import sqlite3

import pytest

from models.parent import Parent
from models.student import Student
from models.teacher import Teacher
from repositories.parent_repository import ParentRepository
from repositories.student_repository import StudentRepository
from repositories.teacher_repository import TeacherRepository


def test_student_get_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            age INTEGER,
            guardian_id INTEGER,
            enrollment_date DATE,
            status TEXT DEFAULT 'active'
        )
    """)

    repository = StudentRepository(connection)

    student = repository.create(
        Student(
            id=None,
            tenant_id="school-A",
            user_id=None,
            name="Student A",
            class_name="JSS 1",
            age=12,
            guardian_id=None,
            enrollment_date=None,
        )
    )

    assert repository.get("school-A", student.id) is not None
    assert repository.get("school-B", student.id) is None

    connection.close()


def test_teacher_get_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            qualification TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    repository = TeacherRepository(connection)

    teacher = repository.create(
        Teacher(
            id=None,
            tenant_id="school-A",
            user_id=None,
            name="Teacher A",
            subject="Mathematics",
            qualification=None,
        )
    )

    assert repository.get("school-A", teacher.id) is not None
    assert repository.get("school-B", teacher.id) is None

    connection.close()


def test_parent_get_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    repository = ParentRepository(connection)

    parent = repository.create(
        Parent(
            id=None,
            tenant_id="school-A",
            user_id=None,
            name="Parent A",
            phone=None,
            email=None,
        )
    )

    assert repository.get("school-A", parent.id) is not None
    assert repository.get("school-B", parent.id) is None

    connection.close()
