import sqlite3

from models.user import User
from repositories.user_repository import UserRepository


def test_create_and_get_user():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
        """
    )

    repository = UserRepository(connection)

    user = User(
        id=None,
        tenant_id="school-001",
        name="KOS User",
        email="user@example.com",
        role="teacher",
    )

    created = repository.create(user)

    assert created.id is not None
    assert created.tenant_id == "school-001"
    assert created.name == "KOS User"
    assert created.email == "user@example.com"
    assert created.role == "teacher"
    assert created.status == "active"

    result = repository.get(created.id)

    assert result is not None
    assert result.id == created.id
    assert result.tenant_id == "school-001"
    assert result.name == "KOS User"
    assert result.email == "user@example.com"
    assert result.role == "teacher"
    assert result.status == "active"

    connection.close()
