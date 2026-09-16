import database

from models.institution_anchor import InstitutionAnchor
from repositories.institution_anchor_repository import InstitutionAnchorRepository


def test_institution_anchor_repository_create_and_get(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)

        anchor = InstitutionAnchor(
            id=None,
            institution_type="church",
            name="Example Church",
            provenance_reference="official-reference",
        )

        created = repository.create(anchor)

        assert created.id is not None
        assert created.institution_type == "church"
        assert created.name == "Example Church"
        assert created.provenance_reference == "official-reference"
        assert created.verification_status == "pending"
        assert created.status == "active"

        fetched = repository.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.institution_type == "church"
        assert fetched.name == "Example Church"
        assert fetched.provenance_reference == "official-reference"
        assert fetched.verification_status == "pending"
        assert fetched.status == "active"

    finally:
        connection.close()


def test_institution_anchor_repository_get_missing_returns_none(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_missing.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)

        assert repository.get(999999) is None

    finally:
        connection.close()


def test_institution_anchor_repository_list_active(tmp_path, monkeypatch):
    db_path = tmp_path / "institution_anchor_active.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)

        active = repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Active Church",
                provenance_reference="church-reference",
            )
        )

        inactive = repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="school",
                name="Inactive School",
                provenance_reference="school-reference",
                status="inactive",
            )
        )

        results = repository.list_active()

        assert [anchor.id for anchor in results] == [active.id]
        assert all(anchor.status == "active" for anchor in results)
        assert inactive.id not in [anchor.id for anchor in results]

    finally:
        connection.close()


def test_institution_anchor_repository_supports_multiple_institution_types(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "institution_anchor_types.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)

    database.init_db()
    connection = database.get_connection()

    try:
        repository = InstitutionAnchorRepository(connection)

        church = repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="church",
                name="Example Church",
                provenance_reference="church-reference",
            )
        )

        school = repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="school",
                name="Example School",
                provenance_reference="school-reference",
            )
        )

        hospital = repository.create(
            InstitutionAnchor(
                id=None,
                institution_type="hospital",
                name="Example Hospital",
                provenance_reference="hospital-reference",
            )
        )

        assert repository.get(church.id).institution_type == "church"
        assert repository.get(school.id).institution_type == "school"
        assert repository.get(hospital.id).institution_type == "hospital"

    finally:
        connection.close()
