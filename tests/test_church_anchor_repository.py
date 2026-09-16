from models.church_anchor import ChurchAnchor
from repositories.church_anchor_repository import ChurchAnchorRepository


def test_create_and_get_church_anchor(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "church_anchor_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        connection.execute(
            """
            INSERT INTO tenants (tenant_id)
            VALUES (?)
            """,
            ("tenant-001",),
        )
        connection.commit()

        repository = ChurchAnchorRepository(connection)

        anchor = ChurchAnchor(
            id=None,
            tenant_id="tenant-001",
            name="Example Church",
            provenance_reference="official-reference",
        )

        created = repository.create(anchor)

        assert created.id is not None
        assert created.tenant_id == "tenant-001"
        assert created.name == "Example Church"
        assert created.provenance_reference == "official-reference"
        assert created.verification_status == "pending"
        assert created.status == "active"

        fetched = repository.get_by_id(created.id)
        assert fetched == created

        fetched_by_tenant = repository.get_by_tenant_id("tenant-001")
        assert fetched_by_tenant == created

    finally:
        connection.close()


def test_list_active_church_anchors(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "church_anchor_list.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        connection.executemany(
            """
            INSERT INTO tenants (tenant_id)
            VALUES (?)
            """,
            [
                ("tenant-001",),
                ("tenant-002",),
            ],
        )
        connection.commit()

        repository = ChurchAnchorRepository(connection)

        repository.create(
            ChurchAnchor(
                id=None,
                tenant_id="tenant-001",
                name="Active Church",
                provenance_reference="reference-001",
            )
        )

        repository.create(
            ChurchAnchor(
                id=None,
                tenant_id="tenant-002",
                name="Inactive Church",
                provenance_reference="reference-002",
                status="inactive",
            )
        )

        active = repository.list_active()

        assert len(active) == 1
        assert active[0].tenant_id == "tenant-001"

    finally:
        connection.close()


def test_get_missing_church_anchor_returns_none(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "church_anchor_missing.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = ChurchAnchorRepository(connection)

        assert repository.get_by_id(999999) is None
        assert repository.get_by_tenant_id("does-not-exist") is None

    finally:
        connection.close()
