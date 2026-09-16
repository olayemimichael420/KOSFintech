import database

from models.institution_anchor import InstitutionAnchor
from repositories.institution_anchor_repository import InstitutionAnchorRepository
from repositories.service_binding_repository import ServiceBindingRepository
from services.service_binding_service import ServiceBindingService


def test_service_binding_service_create_and_get(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_service.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        binding_repository = ServiceBindingRepository(connection)
        service = ServiceBindingService(binding_repository)

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Example Church",
                provenance_reference="official-reference",
            )
        )

        created = service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-001",
        )

        assert created.id is not None
        assert created.institution_anchor_id == anchor.id
        assert created.tenant_id == "tenant-001"
        assert created.status == "active"

        fetched = service.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.institution_anchor_id == anchor.id
        assert fetched.tenant_id == "tenant-001"

    finally:
        connection.close()


def test_service_binding_service_list_active(tmp_path, monkeypatch):
    db_path = tmp_path / "service_binding_service_list.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        institution_repository = InstitutionAnchorRepository(connection)
        binding_repository = ServiceBindingRepository(connection)
        service = ServiceBindingService(binding_repository)

        anchor = institution_repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="school",
                name="Example School",
                provenance_reference="official-reference",
            )
        )

        service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-active",
        )

        service.create(
            institution_anchor_id=anchor.id,
            tenant_id="tenant-inactive",
            status="inactive",
        )

        active = service.list_active()

        assert len(active) == 1
        assert active[0].tenant_id == "tenant-active"
        assert active[0].status == "active"

    finally:
        connection.close()
