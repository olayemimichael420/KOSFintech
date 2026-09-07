import sqlite3

from models.parent import Parent
from repositories.parent_repository import ParentRepository


def test_create_and_get_parent():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
        )
        """
    )

    repository = ParentRepository(connection)

    parent = Parent(
        id=None,
        tenant_id="school-001",
        user_id=1001,
        name="John Doe",
        phone="+2348000000000",
        email="john@example.com",
    )

    created = repository.create(parent)

    assert created.id is not None
    assert created.tenant_id == "school-001"

    result = repository.get("school-001", created.id)

    assert result is not None
    assert result.id == created.id
    assert result.name == "John Doe"
    assert result.phone == "+2348000000000"
    assert result.email == "john@example.com"
    assert result.status == "active"

    connection.close()

def test_parent_repository_list_is_tenant_scoped():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    repository = ParentRepository(connection)

    repository.create(Parent(
        id=None, tenant_id="school-001", user_id=None,
        name="Parent A", phone="+2348000000001",
        email="a@example.test",
    ))
    repository.create(Parent(
        id=None, tenant_id="school-002", user_id=None,
        name="Parent B", phone="+2348000000002",
        email="b@example.test",
    ))

    result = repository.list("school-001")

    assert len(result) == 1
    assert result[0].name == "Parent A"
    assert result[0].tenant_id == "school-001"

    connection.close()
