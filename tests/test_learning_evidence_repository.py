import sqlite3

import database
from models.learning_evidence import LearningEvidence
from repositories.learning_evidence_repository import LearningEvidenceRepository


def _connection(tmp_path, monkeypatch):
    db_path = tmp_path / "learning_evidence_repository.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()

    connection = database.get_connection()
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def _seed_context(connection, tenant_id="tenant-a", person_name="Member A"):
    connection.execute(
        "INSERT INTO tenants (tenant_id) VALUES (?)",
        (tenant_id,),
    )

    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        (person_name,),
    )

    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        (person_name,),
    ).fetchone()[0]

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
            tenant_id,
            f"Church {tenant_id}",
            "test-provenance",
        ),
    )

    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

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
            tenant_id,
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
        (tenant_id, person_id),
    ).fetchone()[0]

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
            tenant_id,
            f"Session {tenant_id}",
            "2026-01-01",
            "2026-12-31",
        ),
    )

    session_id = connection.execute(
        """
        SELECT id
        FROM teaching_sessions
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

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
            tenant_id,
            session_id,
            f"Series {tenant_id}",
            "2026-02-01",
            "2026-10-31",
        ),
    )

    series_id = connection.execute(
        """
        SELECT id
        FROM teaching_series
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

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
            tenant_id,
            series_id,
            f"Focus {tenant_id}",
            "2026-03-01",
            "2026-09-30",
        ),
    )

    focus_id = connection.execute(
        """
        SELECT id
        FROM teaching_focuses
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO teaching_contents (
            tenant_id,
            teaching_focus_id,
            name,
            description,
            sequence,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            focus_id,
            f"Content {tenant_id}",
            "Test teaching content",
            1,
            "active",
        ),
    )

    content_id = connection.execute(
        """
        SELECT id
        FROM teaching_contents
        WHERE tenant_id = ?
        """,
        (tenant_id,),
    ).fetchone()[0]

    connection.commit()

    return membership_id, content_id


def _evidence(
    tenant_id,
    membership_id,
    teaching_content_id,
    date,
    description,
    remark=None,
):
    return LearningEvidence(
        id=None,
        tenant_id=tenant_id,
        membership_id=membership_id,
        teaching_content_id=teaching_content_id,
        evidence_date=date,
        description=description,
        remark=remark,
    )


def test_create_and_get_learning_evidence(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    membership_id, content_id = _seed_context(connection)

    repository = LearningEvidenceRepository(connection)

    created = repository.create(
        _evidence(
            "tenant-a",
            membership_id,
            content_id,
            "2026-09-19",
            "Member submitted a written reflection.",
            "Observable learning evidence.",
        )
    )

    assert created.id is not None

    fetched = repository.get(
        "tenant-a",
        created.id,
    )

    assert fetched == created

    connection.close()


def test_list_by_tenant_is_tenant_scoped(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)

    member_a, content_a = _seed_context(
        connection,
        "tenant-a",
        "Member A",
    )

    member_b, content_b = _seed_context(
        connection,
        "tenant-b",
        "Member B",
    )

    repository = LearningEvidenceRepository(connection)

    repository.create(
        _evidence(
            "tenant-a",
            member_a,
            content_a,
            "2026-09-19",
            "Tenant A evidence.",
        )
    )

    repository.create(
        _evidence(
            "tenant-b",
            member_b,
            content_b,
            "2026-09-19",
            "Tenant B evidence.",
        )
    )

    results = repository.list_by_tenant("tenant-a")

    assert len(results) == 1
    assert results[0].tenant_id == "tenant-a"
    assert results[0].description == "Tenant A evidence."

    connection.close()


def test_list_by_member(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)
    membership_id, content_id = _seed_context(connection)

    connection.execute(
        """
        INSERT INTO teaching_contents (
            tenant_id,
            teaching_focus_id,
            name,
            description,
            sequence,
            status
        )
        SELECT
            tenant_id,
            teaching_focus_id,
            'Second Content',
            'Second test content',
            2,
            'active'
        FROM teaching_contents
        WHERE id = ?
        """,
        (content_id,),
    )

    second_content_id = connection.execute(
        """
        SELECT id
        FROM teaching_contents
        WHERE tenant_id = 'tenant-a'
          AND name = 'Second Content'
        """
    ).fetchone()[0]

    connection.commit()

    repository = LearningEvidenceRepository(connection)

    repository.create(
        _evidence(
            "tenant-a",
            membership_id,
            content_id,
            "2026-09-19",
            "First evidence.",
        )
    )

    repository.create(
        _evidence(
            "tenant-a",
            membership_id,
            second_content_id,
            "2026-09-20",
            "Second evidence.",
        )
    )

    results = repository.list_by_member(
        "tenant-a",
        membership_id,
    )

    assert [item.description for item in results] == [
        "First evidence.",
        "Second evidence.",
    ]

    connection.close()


def test_list_by_content(tmp_path, monkeypatch):
    connection = _connection(tmp_path, monkeypatch)

    member_a, content_id = _seed_context(
        connection,
        "tenant-a",
        "Member A",
    )

    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        ("Member B",),
    )

    person_b = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Member B",),
    ).fetchone()[0]

    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = 'tenant-a'
        """
    ).fetchone()[0]

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
            "tenant-a",
            person_b,
            church_anchor_id,
            "test-provenance",
        ),
    )

    member_b = connection.execute(
        """
        SELECT id
        FROM memberships
        WHERE tenant_id = 'tenant-a'
          AND person_id = ?
        """,
        (person_b,),
    ).fetchone()[0]

    connection.commit()

    repository = LearningEvidenceRepository(connection)

    repository.create(
        _evidence(
            "tenant-a",
            member_a,
            content_id,
            "2026-09-19",
            "First member evidence.",
        )
    )

    repository.create(
        _evidence(
            "tenant-a",
            member_b,
            content_id,
            "2026-09-20",
            "Second member evidence.",
        )
    )

    results = repository.list_by_content(
        "tenant-a",
        content_id,
    )

    assert [item.description for item in results] == [
        "First member evidence.",
        "Second member evidence.",
    ]

    connection.close()


def test_get_returns_none_for_unknown_or_cross_tenant_record(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    membership_id, content_id = _seed_context(connection)

    repository = LearningEvidenceRepository(connection)

    created = repository.create(
        _evidence(
            "tenant-a",
            membership_id,
            content_id,
            "2026-09-19",
            "Tenant-scoped evidence.",
        )
    )

    assert repository.get("tenant-a", 999999) is None
    assert repository.get("tenant-b", created.id) is None

    connection.close()


def test_create_rejects_invalid_parent_relationship(
    tmp_path,
    monkeypatch,
):
    connection = _connection(tmp_path, monkeypatch)

    repository = LearningEvidenceRepository(connection)

    try:
        repository.create(
            _evidence(
                "tenant-a",
                999999,
                999999,
                "2026-09-19",
                "Invalid parent evidence.",
            )
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError(
            "Expected foreign-key enforcement for invalid parents"
        )

    connection.close()
