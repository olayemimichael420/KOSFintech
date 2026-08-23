import sqlite3

from models.user import User
from repositories.user_repository import UserRepository


def test_user_get_is_tenant_scoped():
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

    user = repository.create(
        User(
            id=None,
            tenant_id="school-A",
            name="User A",
            email="user-a@example.com",
            role="teacher",
        )
    )

    assert repository.get("school-A", user.id) is not None
    assert repository.get("school-B", user.id) is None

    connection.close()
