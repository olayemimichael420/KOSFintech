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
