import sqlite3

import database
import pytest


def _setup_fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "core_relationship_fk.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    return database.get_connection()


def test_parents_enforce_user_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO parents (tenant_id, user_id, name)
                VALUES (?, ?, ?)
                """,
                ("school-001", 999999, "Test Parent"),
            )
    finally:
        connection.close()


def test_teachers_enforce_user_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teachers (tenant_id, user_id, name, subject)
                VALUES (?, ?, ?, ?)
                """,
                ("school-001", 999999, "Test Teacher", "Mathematics"),
            )
    finally:
        connection.close()


def test_students_enforce_user_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO students (tenant_id, user_id, name, class_name)
                VALUES (?, ?, ?, ?)
                """,
                ("school-001", 999999, "Test Student", "JSS1"),
            )
    finally:
        connection.close()


def test_students_enforce_guardian_foreign_key(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO students (
                    tenant_id, name, class_name, guardian_id
                )
                VALUES (?, ?, ?, ?)
                """,
                ("school-001", "Test Student", "JSS1", 999999),
            )
    finally:
        connection.close()

def test_teacher_rejects_cross_tenant_user(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            INSERT INTO users (
                tenant_id, name, email, role, status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-002",
                "School Two Teacher",
                "teacher@school-two.test",
                "teacher",
                "active",
            ),
        )

        user_id = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND email = ?
            """,
            (
                "school-002",
                "teacher@school-two.test",
            ),
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO teachers (
                    tenant_id, user_id, name, subject
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "school-001",
                    user_id,
                    "Cross Tenant Teacher",
                    "Mathematics",
                ),
            )
    finally:
        connection.close()


def test_student_rejects_cross_tenant_user(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            INSERT INTO users (
                tenant_id, name, email, role, status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-002",
                "School Two Student",
                "student@school-two.test",
                "student",
                "active",
            ),
        )

        user_id = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND email = ?
            """,
            (
                "school-002",
                "student@school-two.test",
            ),
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO students (
                    tenant_id, user_id, name, class_name
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "school-001",
                    user_id,
                    "Cross Tenant Student",
                    "JSS1",
                ),
            )
    finally:
        connection.close()


def test_parent_rejects_cross_tenant_user(tmp_path, monkeypatch):
    connection = _setup_fresh_db(tmp_path, monkeypatch)
    try:
        connection.execute(
            """
            INSERT INTO users (
                tenant_id, name, email, role, status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "school-002",
                "School Two Parent",
                "parent@school-two.test",
                "parent",
                "active",
            ),
        )

        user_id = connection.execute(
            """
            SELECT id
            FROM users
            WHERE tenant_id = ?
              AND email = ?
            """,
            (
                "school-002",
                "parent@school-two.test",
            ),
        ).fetchone()["id"]

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO parents (
                    tenant_id, user_id, name
                )
                VALUES (?, ?, ?)
                """,
                (
                    "school-001",
                    user_id,
                    "Cross Tenant Parent",
                ),
            )
    finally:
        connection.close()
