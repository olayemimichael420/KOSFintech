import pytest

import database
from models.assessment import Assessment
from models.assessment_score import AssessmentScore
from repositories.assessment_repository import AssessmentRepository
from repositories.assessment_score_repository import AssessmentScoreRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "assessment_score_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _seed(connection):
    connection.execute(
        "INSERT OR IGNORE INTO tenants (tenant_id) VALUES (?)",
        ("tenant-cmos",),
    )

    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        ("Assessment Score Test Person",),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Assessment Score Test Person",),
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
            "Assessment Score Test Church",
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
        ("tenant-cmos", "Assessment Score Test Church"),
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
            "Assessment Score Session",
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
        ("tenant-cmos", "Assessment Score Session"),
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
            "Assessment Score Series",
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
            "Assessment Score Series",
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
            "Assessment Score Focus",
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
            "Assessment Score Focus",
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
            "Assessment Score Content",
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
            "Assessment Score Content",
        ),
    ).fetchone()["id"]

    assessment_repository = AssessmentRepository(connection)
    assessment = assessment_repository.create(
        Assessment(
            id=None,
            tenant_id="tenant-cmos",
            teaching_content_id=teaching_content_id,
            name="Assessment Score Review",
            description="Assessment used for score repository tests.",
            assessment_date="2026-09-19",
        )
    )

    connection.commit()

    return assessment.id, membership_id


def test_create_and_get_assessment_score(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        score = AssessmentScore(
            id=None,
            tenant_id="tenant-cmos",
            assessment_id=assessment_id,
            membership_id=membership_id,
            score=82,
            scored_date="2026-09-19",
            remark="Observable response recorded.",
        )

        created = repository.create(score)
        fetched = repository.get("tenant-cmos", created.id)

        assert created.id is not None
        assert fetched == created
    finally:
        connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        created = repository.create(
            AssessmentScore(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                score=75,
                scored_date="2026-09-19",
            )
        )

        assert repository.get("other-tenant", created.id) is None
    finally:
        connection.close()


def test_list_by_tenant_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        first = repository.create(
            AssessmentScore(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                score=70,
                scored_date="2026-09-19",
            )
        )

        connection.execute(
            "INSERT INTO persons (name) VALUES (?)",
            ("Assessment Score Second Person",),
        )
        second_person_id = connection.execute(
            "SELECT id FROM persons WHERE name = ?",
            ("Assessment Score Second Person",),
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
            AssessmentScore(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=second_membership_id,
                score=88,
                scored_date="2026-09-20",
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


def test_list_by_assessment_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        created = repository.create(
            AssessmentScore(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                score=91,
                scored_date="2026-09-19",
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


def test_list_by_member_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        created = repository.create(
            AssessmentScore(
                id=None,
                tenant_id="tenant-cmos",
                assessment_id=assessment_id,
                membership_id=membership_id,
                score=96,
                scored_date="2026-09-19",
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


def test_unknown_assessment_score_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        _seed(connection)
        repository = AssessmentScoreRepository(connection)

        assert repository.get("tenant-cmos", 999999) is None
    finally:
        connection.close()


def test_duplicate_assessment_score_for_member_is_rejected(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)
        repository = AssessmentScoreRepository(connection)

        score = AssessmentScore(
            id=None,
            tenant_id="tenant-cmos",
            assessment_id=assessment_id,
            membership_id=membership_id,
            score=82,
            scored_date="2026-09-19",
        )

        repository.create(score)

        with pytest.raises(Exception):
            repository.create(score)
    finally:
        connection.close()


def test_cross_tenant_assessment_reference_is_rejected(
    monkeypatch,
    tmp_path,
):
    connection = _connection(monkeypatch, tmp_path)
    try:
        assessment_id, membership_id = _seed(connection)

        connection.execute(
            """
            INSERT INTO tenants (tenant_id)
            VALUES ('tenant-other')
            """
        )
        connection.commit()

        repository = AssessmentScoreRepository(connection)

        with pytest.raises(Exception):
            repository.create(
                AssessmentScore(
                    id=None,
                    tenant_id="tenant-other",
                    assessment_id=assessment_id,
                    membership_id=membership_id,
                    score=80,
                    scored_date="2026-09-19",
                )
            )
    finally:
        connection.close()
