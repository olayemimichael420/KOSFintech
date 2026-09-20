import database

from models.progress import Progress
from repositories.progress_repository import ProgressRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "progress_repository.db"
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
        ("Progress Test Person",),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Progress Test Person",),
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
            "Progress Test Church",
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
        ("tenant-cmos", "Progress Test Church"),
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
            "Progress Session",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    session_id = connection.execute(
        """
        SELECT id
        FROM teaching_sessions
        WHERE tenant_id = ?
          AND name = ?
        """,
        ("tenant-cmos", "Progress Session"),
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
            session_id,
            "Progress Series",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    series_id = connection.execute(
        """
        SELECT id
        FROM teaching_series
        WHERE tenant_id = ?
          AND teaching_session_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            session_id,
            "Progress Series",
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
            series_id,
            "Progress Focus",
            "2026-09-01",
            "2026-12-31",
        ),
    )
    focus_id = connection.execute(
        """
        SELECT id
        FROM teaching_focuses
        WHERE tenant_id = ?
          AND teaching_series_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            series_id,
            "Progress Focus",
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
            focus_id,
            "Progress Content",
        ),
    )
    content_id = connection.execute(
        """
        SELECT id
        FROM teaching_contents
        WHERE tenant_id = ?
          AND teaching_focus_id = ?
          AND name = ?
        """,
        (
            "tenant-cmos",
            focus_id,
            "Progress Content",
        ),
    ).fetchone()["id"]

    connection.commit()

    return membership_id, content_id


def test_create_and_get_progress(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        membership_id, content_id = _seed(connection)
        repository = ProgressRepository(connection)

        progress = Progress(
            id=None,
            tenant_id="tenant-cmos",
            membership_id=membership_id,
            teaching_content_id=content_id,
            progress_date="2026-09-19",
            description="Demonstrated increased understanding",
            remark="Recorded during follow-up.",
        )

        created = repository.create(progress)
        fetched = repository.get("tenant-cmos", created.id)

        assert created.id is not None
        assert fetched == created
    finally:
        connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        membership_id, content_id = _seed(connection)
        repository = ProgressRepository(connection)

        created = repository.create(
            Progress(
                id=None,
                tenant_id="tenant-cmos",
                membership_id=membership_id,
                teaching_content_id=content_id,
                progress_date="2026-09-19",
                description="Recorded learning development",
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
        membership_id, content_id = _seed(connection)
        repository = ProgressRepository(connection)

        first = repository.create(
            Progress(
                id=None,
                tenant_id="tenant-cmos",
                membership_id=membership_id,
                teaching_content_id=content_id,
                progress_date="2026-09-20",
                description="Second progress record",
            )
        )

        second = repository.create(
            Progress(
                id=None,
                tenant_id="tenant-cmos",
                membership_id=membership_id,
                teaching_content_id=content_id,
                progress_date="2026-09-19",
                description="First progress record",
            )
        )

        rows = repository.list_by_tenant("tenant-cmos")

        assert [row.id for row in rows] == [second.id, first.id]
        assert all(row.tenant_id == "tenant-cmos" for row in rows)
        assert repository.list_by_tenant("other-tenant") == []
    finally:
        connection.close()


def test_list_by_member(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        membership_id, content_id = _seed(connection)
        repository = ProgressRepository(connection)

        created = repository.create(
            Progress(
                id=None,
                tenant_id="tenant-cmos",
                membership_id=membership_id,
                teaching_content_id=content_id,
                progress_date="2026-09-19",
                description="Member progress",
            )
        )

        rows = repository.list_by_member(
            "tenant-cmos",
            membership_id,
        )

        assert [row.id for row in rows] == [created.id]
        assert repository.list_by_member(
            "other-tenant",
            membership_id,
        ) == []
    finally:
        connection.close()


def test_list_by_content(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    try:
        membership_id, content_id = _seed(connection)
        repository = ProgressRepository(connection)

        created = repository.create(
            Progress(
                id=None,
                tenant_id="tenant-cmos",
                membership_id=membership_id,
                teaching_content_id=content_id,
                progress_date="2026-09-19",
                description="Content progress",
            )
        )

        rows = repository.list_by_content(
            "tenant-cmos",
            content_id,
        )

        assert [row.id for row in rows] == [created.id]
        assert repository.list_by_content(
            "other-tenant",
            content_id,
        ) == []
    finally:
        connection.close()
