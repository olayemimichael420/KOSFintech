import database

from models.assessment import Assessment
from repositories.assessment_repository import AssessmentRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "assessment_repository.db"
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
        ("Assessment Test Person",),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Assessment Test Person",),
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
            "Assessment Test Church",
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
        ("tenant-cmos", "Assessment Test Church"),
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
            "Assessment Session",
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
        ("tenant-cmos", "Assessment Session"),
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
            "Assessment Series",
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
            "Assessment Series",
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
            "Assessment Focus",
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
            "Assessment Focus",
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
            "Assessment Content",
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
            "Assessment Content",
        ),
    ).fetchone()["id"]

    connection.commit()
    return teaching_content_id


def test_create_and_get_assessment(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)
        repository = AssessmentRepository(connection)

        assessment = Assessment(
            id=None,
            tenant_id="tenant-cmos",
            teaching_content_id=teaching_content_id,
            name="Understanding Review",
            description="Review of the taught material.",
            assessment_date="2026-09-19",
        )

        created = repository.create(assessment)
        fetched = repository.get("tenant-cmos", created.id)

        assert created.id is not None
        assert fetched == created
    finally:
        connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)
        repository = AssessmentRepository(connection)

        created = repository.create(
            Assessment(
                id=None,
                tenant_id="tenant-cmos",
                teaching_content_id=teaching_content_id,
                name="Tenant Scoped Assessment",
                assessment_date="2026-09-19",
            )
        )

        assert repository.get("other-tenant", created.id) is None
    finally:
        connection.close()


def test_list_by_tenant_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)
        repository = AssessmentRepository(connection)

        first = repository.create(
            Assessment(
                id=None,
                tenant_id="tenant-cmos",
                teaching_content_id=teaching_content_id,
                name="Assessment A",
                assessment_date="2026-09-19",
            )
        )

        second = repository.create(
            Assessment(
                id=None,
                tenant_id="tenant-cmos",
                teaching_content_id=teaching_content_id,
                name="Assessment B",
                assessment_date="2026-09-20",
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


def test_list_by_content_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)
        repository = AssessmentRepository(connection)

        first = repository.create(
            Assessment(
                id=None,
                tenant_id="tenant-cmos",
                teaching_content_id=teaching_content_id,
                name="Content Assessment A",
                assessment_date="2026-09-19",
            )
        )

        second = repository.create(
            Assessment(
                id=None,
                tenant_id="tenant-cmos",
                teaching_content_id=teaching_content_id,
                name="Content Assessment B",
                assessment_date="2026-09-20",
            )
        )

        results = repository.list_by_content(
            "tenant-cmos",
            teaching_content_id,
        )

        assert [item.id for item in results] == [
            first.id,
            second.id,
        ]
        assert repository.list_by_content(
            "other-tenant",
            teaching_content_id,
        ) == []
    finally:
        connection.close()


def test_unknown_assessment_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)
        repository = AssessmentRepository(connection)

        assert repository.get("tenant-cmos", 999999) is None
    finally:
        connection.close()


def test_cross_tenant_content_reference_is_rejected(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        teaching_content_id = _seed(connection)

        connection.execute(
            """
            INSERT INTO tenants (tenant_id)
            VALUES ('tenant-other')
            """
        )

        connection.commit()

        repository = AssessmentRepository(connection)

        assessment = Assessment(
            id=None,
            tenant_id="tenant-other",
            teaching_content_id=teaching_content_id,
            name="Invalid Cross Tenant Assessment",
            assessment_date="2026-09-19",
        )

        try:
            repository.create(assessment)
            assert False, "Expected cross-tenant FK rejection"
        except Exception:
            pass
    finally:
        connection.close()
