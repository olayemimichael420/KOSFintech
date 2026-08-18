from models.administration import Administration
from repositories.administration_repository import AdministrationRepository


def test_create_and_get_administration(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "administration_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = AdministrationRepository(connection)

        administration = Administration(
            id=None,
            tenant_id="tenant-001",
            name="Example School",
            administration_type="school",
        )

        created = repository.create(administration)

        assert created.id is not None
        assert created.tenant_id == "tenant-001"
        assert created.name == "Example School"
        assert created.administration_type == "school"
        assert created.status == "active"

        fetched = repository.get_by_id(created.id)

        assert fetched == created

        fetched_by_tenant = repository.get_by_tenant_id(
            "tenant-001"
        )

        assert fetched_by_tenant == created

    finally:
        connection.close()


def test_list_active_administrations(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "administration_list.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = AdministrationRepository(connection)

        repository.create(
            Administration(
                id=None,
                tenant_id="tenant-001",
                name="Active School",
                administration_type="school",
            )
        )

        repository.create(
            Administration(
                id=None,
                tenant_id="tenant-002",
                name="Suspended Hospital",
                administration_type="hospital",
                status="suspended",
            )
        )

        active = repository.list_active()

        assert len(active) == 1
        assert active[0].tenant_id == "tenant-001"

    finally:
        connection.close()


def test_get_missing_administration_returns_none(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "administration_missing.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = AdministrationRepository(connection)

        assert repository.get_by_id(999999) is None
        assert repository.get_by_tenant_id("does-not-exist") is None

    finally:
        connection.close()
