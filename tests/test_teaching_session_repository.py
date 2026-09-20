import sqlite3

from models.teaching_session import TeachingSession
from repositories.teaching_session_repository import TeachingSessionRepository


def _repository():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE teaching_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            UNIQUE (tenant_id, name)
        )
        """
    )
    connection.commit()

    return connection, TeachingSessionRepository(connection)


def test_create_persists_and_returns_teaching_session():
    connection, repository = _repository()

    session = repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="2026 Teaching Session",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    assert session.id is not None
    assert session.tenant_id == "tenant-1"
    assert session.name == "2026 Teaching Session"

    row = connection.execute(
        "SELECT * FROM teaching_sessions WHERE id = ?",
        (session.id,),
    ).fetchone()

    assert row["tenant_id"] == "tenant-1"
    assert row["name"] == "2026 Teaching Session"


def test_get_is_tenant_scoped():
    connection, repository = _repository()

    session = repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="Session A",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    assert repository.get("tenant-1", session.id) == session
    assert repository.get("tenant-2", session.id) is None


def test_list_is_tenant_scoped_and_ordered():
    connection, repository = _repository()

    repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="Later",
            start_date="2026-06-01",
            end_date="2026-12-31",
        )
    )
    repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="Earlier",
            start_date="2026-01-01",
            end_date="2026-05-31",
        )
    )
    repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-2",
            name="Other Tenant",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    sessions = repository.list("tenant-1")

    assert [session.name for session in sessions] == [
        "Earlier",
        "Later",
    ]
    assert all(session.tenant_id == "tenant-1" for session in sessions)


def test_create_rejects_duplicate_name_within_tenant():
    connection, repository = _repository()

    session = TeachingSession(
        id=None,
        tenant_id="tenant-1",
        name="2026 Teaching Session",
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    repository.create(session)

    try:
        repository.create(session)
        assert False, "duplicate tenant/name should be rejected"
    except sqlite3.IntegrityError:
        pass


def test_same_name_is_allowed_for_different_tenants():
    connection, repository = _repository()

    first = repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-1",
            name="2026 Teaching Session",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    second = repository.create(
        TeachingSession(
            id=None,
            tenant_id="tenant-2",
            name="2026 Teaching Session",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
    )

    assert first.id != second.id
    assert first.name == second.name
    assert first.tenant_id != second.tenant_id


def test_create_rejects_unknown_tenant():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        CREATE TABLE tenants (
            tenant_id TEXT PRIMARY KEY
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE teaching_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (tenant_id)
                REFERENCES tenants(tenant_id),
            UNIQUE (tenant_id, name)
        )
        """
    )

    repository = TeachingSessionRepository(connection)

    try:
        repository.create(
            TeachingSession(
                id=None,
                tenant_id="missing-tenant",
                name="2026 Teaching Session",
                start_date="2026-01-01",
                end_date="2026-12-31",
            )
        )
        assert False, "unknown tenant should be rejected"
    except sqlite3.IntegrityError:
        pass
