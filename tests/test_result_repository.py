import sqlite3

import pytest

import database
from models.assessment import Assessment
from models.grade import Grade
from models.result import Result
from repositories.assessment_repository import AssessmentRepository
from repositories.grade_repository import GradeRepository
from repositories.result_repository import ResultRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "result_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed(connection):
    connection.execute(
        "INSERT INTO tenants (tenant_id) VALUES (?)",
        ("tenant-cmos",),
    )

    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        ("Result Test Person",),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Result Test Person",),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO church_anchors (
            tenant_id,
            name,
            provenance_reference
        )
        VALUES (?, ?, ?)
        """,
        (
            "tenant-cmos",
            "Result Test Church",
            "test-provenance",
        ),
    )
    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = ?
          AND name = ?
        """,
        ("tenant-cmos", "Result Test Church"),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO memberships (
            tenant_id,
            person_id,
            church_anchor_id,
            provenance_reference
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "tenant-cmos",
            person_id,
            church_anchor_id,
            "test-provenance",
        ),
    )
    membership_id = connection.execute(
        """
        SELECT id
        FROM memberships
        WHERE tenant_id = ?
          AND person_id = ?
        """,
        ("tenant-cmos", person_id),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "tenant-cmos",
            "Result Session",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    teaching_session_id = connection.execute(
        """
        SELECT id
        FROM teaching_sessions
        WHERE tenant_id = ?
          AND name = ?
        """,
        ("tenant-cmos", "Result Session"),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_series (
            tenant_id,
            teaching_session_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-cmos",
            teaching_session_id,
            "Result Series",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    teaching_series_id = connection.execute(
        """
        SELECT id
        FROM teaching_series
        WHERE tenant_id = ?
          AND teaching_session_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            teaching_session_id,
            "Result Series",
        ),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_focuses (
            tenant_id,
            teaching_series_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "tenant-cmos",
            teaching_series_id,
            "Result Focus",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    teaching_focus_id = connection.execute(
        """
        SELECT id
        FROM teaching_focuses
        WHERE tenant_id = ?
          AND teaching_series_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            teaching_series_id,
            "Result Focus",
        ),
    ).fetchone()["id"]

    connection.execute(
        """
        INSERT INTO teaching_contents (
            tenant_id,
            teaching_focus_id,
            name
        )
        VALUES (?, ?, ?)
        """,
        (
            "tenant-cmos",
            teaching_focus_id,
            "Result Content",
        ),
    )
    teaching_content_id = connection.execute(
        """
        SELECT id
        FROM teaching_contents
        WHERE tenant_id = ?
          AND teaching_focus_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            teaching_focus_id,
            "Result Content",
        ),
    ).fetchone()["id"]

    assessment = AssessmentRepository(connection).create(
        Assessment(
            id=None,
            tenant_id="tenant-cmos",
            teaching_content_id=teaching_content_id,
            name="Result Assessment",
            description="Assessment used for result repository tests.",
            assessment_date="2026-09-19",
        )
    )

    grade = GradeRepository(connection).create(
        Grade(
            id=None,
            tenant_id="tenant-cmos",
            name="A",
            description="Excellent",
            minimum_score=80,
            maximum_score=100,
        )
    )

    connection.commit()

    return assessment.id, membership_id, grade.id


def test_create_and_get_result(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        result = Result(
            id=None,
            tenant_id="tenant-cmos",
            assessment_id=assessment_id,
            membership_id=membership_id,
            grade_id=grade_id,
            result="Demonstrated understanding of the teaching content",
            result_date="2026-09-19",
            remark="Recorded learning outcome.",
        )

        created = repository.create(result)
        fetched = repository.get("tenant-cmos", created.id)

        assert created.id is not None
        assert fetched == created
    finally:
        connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        created = repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                grade_id=grade_id,
                result="Completed the assessment requirements",
                result_date="2026-09-19",
            )
        )

        assert repository.get("other-tenant", created.id) is None
    finally:
        connection.close()


def test_list_by_tenant_is_tenant_scoped_and_ordered(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        first = repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                grade_id=grade_id,
                result="First recorded result",
                result_date="2026-09-19",
            )
        )

        connection.execute(
            "INSERT INTO persons (name) VALUES (?)",
            ("Result Second Person",),
        )
        second_person_id = connection.execute(
            "SELECT id FROM persons WHERE name = ?",
            ("Result Second Person",),
        ).fetchone()["id"]

        church_anchor_id = connection.execute(
            """
            SELECT id
            FROM church_anchors
            WHERE tenant_id = ?
            LIMIT 1
            """,
            ("tenant-cmos",),
        ).fetchone()["id"]

        connection.execute(
            """
            INSERT INTO memberships (
                tenant_id,
                person_id,
                church_anchor_id,
                provenance_reference
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "tenant-cmos",
                second_person_id,
                church_anchor_id,
                "test-provenance",
            ),
        )

        second_membership_id = connection.execute(
            """
            SELECT id
            FROM memberships
            WHERE tenant_id = ?
              AND person_id = ?
            """,
            ("tenant-cmos", second_person_id),
        ).fetchone()["id"]

        second = repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=second_membership_id,
                grade_id=grade_id,
                result="Second recorded result",
                result_date="2026-09-20",
            )
        )

        results = repository.list_by_tenant("tenant-cmos")

        assert [item.id for item in results] == [
            first.id,
            second.id,
        ]
        assert repository.list_by_tenant("other-tenant") == []
    finally:
        connection.close()


def test_list_by_assessment_is_tenant_scoped(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        created = repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                grade_id=grade_id,
                result="Assessment-specific result",
                result_date="2026-09-19",
            )
        )

        results = repository.list_by_assessment(
            "tenant-cmos",
            assessment_id,
        )

        assert [item.id for item in results] == [created.id]
        assert repository.list_by_assessment(
            "other-tenant",
            assessment_id,
        ) == []
    finally:
        connection.close()


def test_list_by_member_is_tenant_scoped(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        created = repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                grade_id=grade_id,
                result="Member-specific result",
                result_date="2026-09-19",
            )
        )

        results = repository.list_by_member(
            "tenant-cmos",
            membership_id,
        )

        assert [item.id for item in results] == [created.id]
        assert repository.list_by_member(
            "other-tenant",
            membership_id,
        ) == []
    finally:
        connection.close()


def test_result_is_unique_per_assessment_member(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id, grade_id = _seed(connection)
        repository = ResultRepository(connection)

        repository.create(
            Result(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                grade_id=grade_id,
                result="First result",
                result_date="2026-09-19",
            )
        )

        with pytest.raises(sqlite3.IntegrityError):
            repository.create(
                Result(
                    id=None,
                    tenant_id="tenant-cmos",
                    assessment_id=assessment_id,
                    membership_id=membership_id,
                    grade_id=grade_id,
                    result="Duplicate result",
                    result_date="2026-09-20",
                )
            )
    finally:
        connection.close()
