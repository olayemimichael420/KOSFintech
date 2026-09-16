import database

from models.institution_anchor import InstitutionAnchor
from repositories.institution_anchor_repository import InstitutionAnchorRepository
from services.institution_anchor_service import InstitutionAnchorService


def test_institution_anchor_service_create_and_get(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_service.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)
        service = InstitutionAnchorService(repository)

        created = service.create(
            institution_type="church",
            name="Example Church",
            provenance_reference="official-reference",
        )

        assert created.id is not None
        assert created.institution_type == "church"
        assert created.name == "Example Church"
        assert created.provenance_reference == "official-reference"
        assert created.verification_status == "pending"
        assert created.status == "active"

        fetched = service.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.institution_type == "church"
        assert fetched.name == "Example Church"

    finally:
        connection.close()


def test_institution_anchor_service_list_active(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_service_active.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)
        service = InstitutionAnchorService(repository)

        active = service.create(
            institution_type="church",
            name="Active Church",
            provenance_reference="church-reference",
        )

        service.create(
            institution_type="school",
            name="Inactive School",
            provenance_reference="school-reference",
            status="inactive",
        )

        results = service.list_active()

        assert [anchor.id for anchor in results] == [active.id]

    finally:
        connection.close()


def test_institution_anchor_service_rejects_invalid_verification_status(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "institution_anchor_invalid_verification.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)
        service = InstitutionAnchorService(repository)

        try:
            service.create(
                institution_type="church",
                name="Invalid Church",
                provenance_reference="reference",
                verification_status="invalid",
            )
            assert False, "invalid verification_status was accepted"
        except ValueError as exc:
            assert str(exc) == "invalid verification status"

    finally:
        connection.close()


def test_institution_anchor_service_rejects_invalid_status(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "institution_anchor_invalid_status.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)
        service = InstitutionAnchorService(repository)

        try:
            service.create(
                institution_type="church",
                name="Invalid Church",
                provenance_reference="reference",
                status="invalid",
            )
            assert False, "invalid status was accepted"
        except ValueError as exc:
            assert str(exc) == "invalid institution anchor status"

    finally:
        connection.close()
