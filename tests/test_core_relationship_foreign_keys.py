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
