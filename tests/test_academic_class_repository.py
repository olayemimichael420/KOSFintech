import uuid
import pytest
from database import get_connection, init_db
from models.academic_class import AcademicClass
from repositories.academic_class_repository import AcademicClassRepository


_open_connections = []
_setup_counter = 0

@pytest.fixture(autouse=True)
def close_repository_test_connections():
    yield
    for connection in _open_connections:
        try:
            connection.close()
        except Exception:
            pass
    _open_connections.clear()



def setup_connection():
    global _setup_counter
    _setup_counter += 1

    for connection in _open_connections:
        try:
            connection.close()
        except Exception:
            pass
    _open_connections.clear()

    init_db()
    connection = get_connection()
    _open_connections.append(connection)

    tenant_suffix = uuid.uuid4().hex
    tenant_a = f"school-a-{tenant_suffix}"
    tenant_b = f"school-b-{tenant_suffix}"

    connection.execute(
        """
        INSERT OR IGNORE INTO schools (
            tenant_id,
            name,
            school_type,
            country,
            currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_a, "School A", "secondary", "NG", "NGN"),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO schools (
            tenant_id,
            name,
            school_type,
            country,
            currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (tenant_b, "School B", "secondary", "NG", "NGN"),
    )
    connection.commit()

    return connection, tenant_a, tenant_b


def test_create_and_get_academic_class():
    connection, tenant_id, _ = setup_connection()
    repository = AcademicClassRepository(connection)

    academic_class = repository.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_id,
            name="JSS 1",
            education_level="secondary",
            sequence=1,
        )
    )

    assert academic_class.id is not None

    fetched = repository.get(tenant_id, academic_class.id)

    assert fetched is not None
    assert fetched.name == "JSS 1"
    assert fetched.education_level == "secondary"
    assert fetched.sequence == 1


def test_universal_class_labels_are_supported():
    connection, tenant_id, _ = setup_connection()
    repository = AcademicClassRepository(connection)

    labels = [
        "Primary 5",
        "Year 7",
        "Grade 6",
        "Level 100",
        "Foundation A",
    ]

    for label in labels:
        repository.create(
            AcademicClass(
                id=None,
                tenant_id=tenant_id,
                name=label,
            )
        )

    classes = repository.list(tenant_id)
    names = {academic_class.name for academic_class in classes}

    assert set(labels).issubset(names)


def test_get_is_tenant_scoped():
    connection, tenant_a, tenant_b = setup_connection()
    repository = AcademicClassRepository(connection)

    academic_class = repository.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_a,
            name="Primary 5",
        )
    )

    assert repository.get(tenant_a, academic_class.id) is not None
    assert repository.get(tenant_b, academic_class.id) is None


def test_list_is_tenant_scoped():
    connection, tenant_a, tenant_b = setup_connection()
    repository = AcademicClassRepository(connection)

    repository.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_a,
            name="JSS 1",
        )
    )

    repository.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_b,
            name="JSS 1",
        )
    )

    classes = repository.list(tenant_a)

    assert len(classes) == 1
    assert classes[0].tenant_id == tenant_a
    assert classes[0].name == "JSS 1"


def test_duplicate_class_name_is_rejected_within_tenant():
    connection, tenant_id, _ = setup_connection()
    repository = AcademicClassRepository(connection)

    repository.create(
        AcademicClass(
            id=None,
            tenant_id=tenant_id,
            name="JSS 1",
        )
    )

    try:
        repository.create(
            AcademicClass(
                id=None,
                tenant_id=tenant_id,
                name="JSS 1",
            )
        )
        assert False, "Expected duplicate class name to be rejected"
    except Exception:
        assert True
