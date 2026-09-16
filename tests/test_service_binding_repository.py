import database

from models.institution_anchor import InstitutionAnchor
from models.service_binding import ServiceBinding
from models.tenant import Tenant
from repositories.institution_anchor_repository import InstitutionAnchorRepository
from repositories.service_binding_repository import ServiceBindingRepository
from repositories.tenant_repository import TenantRepository


def test_service_binding_repository_create_and_get(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        repository = ServiceBindingRepository(connection)
        tenant_repository = TenantRepository(connection)

        tenant_repository.create(
            Tenant(
                id=None,
                tenant_id="tenant-001",
            )
        )

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Example Church",
                provenance_reference="official-reference",
            )
        )

        binding = ServiceBinding(
            id=None,
            institution_anchor_id=anchor.id,
            tenant_id="tenant-001",
        )

        created = repository.create(binding)

        assert created.id is not None
        assert created.institution_anchor_id == anchor.id
        assert created.tenant_id == "tenant-001"
        assert created.status == "active"

        fetched = repository.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.institution_anchor_id == anchor.id
        assert fetched.tenant_id == "tenant-001"
        assert fetched.status == "active"

    finally:
        connection.close()


def test_service_binding_repository_get_missing_returns_none(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "service_binding_repository_missing.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = ServiceBindingRepository(connection)

        assert repository.get(999999) is None

    finally:
        connection.close()


def test_service_binding_repository_list_active(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_repository_list.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        repository = ServiceBindingRepository(connection)
        tenant_repository = TenantRepository(connection)

        tenant_repository.create(
            Tenant(
                id=None,
                tenant_id="tenant-active",
            )
        )
        tenant_repository.create(
            Tenant(
                id=None,
                tenant_id="tenant-inactive",
                status="inactive",
            )
        )

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Example Church",
                provenance_reference="official-reference",
            )
        )

        repository.create(
            ServiceBinding(
                id=None,
                institution_anchor_id=anchor.id,
                tenant_id="tenant-active",
                status="active",
            )
        )

        repository.create(
            ServiceBinding(
                id=None,
                institution_anchor_id=anchor.id,
                tenant_id="tenant-inactive",
                status="inactive",
            )
        )

        active = repository.list_active()

        assert len(active) == 1
        assert active[0].tenant_id == "tenant-active"
        assert active[0].status == "active"

    finally:
        connection.close()
