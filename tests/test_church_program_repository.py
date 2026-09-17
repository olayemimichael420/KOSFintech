import sqlite3

import database
from models.church_program import ChurchProgram
from repositories.church_program_repository import ChurchProgramRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "church_program_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        ("tenant-a",),
    )
    connection.execute(
        """
        INSERT INTO tenants (tenant_id, status)
        VALUES (?, 'active')
        """,
        ("tenant-b",),
    )
    connection.commit()

    return connection


def test_create_and_get(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchProgramRepository(connection)

    created = repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-a",
            name="Discipleship",
            description="Discipleship program",
            program_type="discipleship",
        )
    )

    assert created.id is not None
    assert created.tenant_id == "tenant-a"
    assert created.name == "Discipleship"

    loaded = repository.get("tenant-a", created.id)

    assert loaded == created

    connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchProgramRepository(connection)

    created = repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-a",
            name="Bible Study",
        )
    )

    assert repository.get("tenant-a", created.id) == created
    assert repository.get("tenant-b", created.id) is None

    connection.close()


def test_list_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchProgramRepository(connection)

    repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-a",
            name="Program A",
        )
    )
    repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-a",
            name="Program B",
        )
    )
    repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-b",
            name="Other Program",
        )
    )

    programs = repository.list("tenant-a")

    assert [program.name for program in programs] == [
        "Program A",
        "Program B",
    ]
    assert all(program.tenant_id == "tenant-a" for program in programs)

    connection.close()


def test_missing_program_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchProgramRepository(connection)

    assert repository.get("tenant-a", 999999) is None

    connection.close()


def test_duplicate_name_is_tenant_local(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = ChurchProgramRepository(connection)

    first = repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-a",
            name="Training",
        )
    )
    second = repository.create(
        ChurchProgram(
            id=None,
            tenant_id="tenant-b",
            name="Training",
        )
    )

    assert first.id != second.id

    try:
        repository.create(
            ChurchProgram(
                id=None,
                tenant_id="tenant-a",
                name="Training",
            )
        )
        assert False, "duplicate program name should be rejected within tenant"
    except Exception as exc:
        assert "UNIQUE" in str(exc).upper()

    connection.close()
