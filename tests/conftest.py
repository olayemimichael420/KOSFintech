import database
import pytest


@pytest.fixture
def db_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "talent_point_repository.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: db_path,
    )

    database.init_db()

    connection = database.get_connection()

    try:
        # Create the users required by the TP repository tests.
        user_1 = connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-1", "User One", "member"),
        ).lastrowid

        user_2 = connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-1", "User Two", "member"),
        ).lastrowid

        # Create service acts required by the TP repository tests.
        connection.execute(
            """
            INSERT INTO service_acts (
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-1",
                user_1,
                user_2,
                "Test Service Act 1",
                "Test service act one",
            ),
        )

        connection.execute(
            """
            INSERT INTO service_acts (
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-1",
                user_2,
                user_1,
                "Test Service Act 2",
                "Test service act two",
            ),
        )

        # Create second tenant for tenant-isolation tests.
        user_3 = connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-2", "User Three", "member"),
        ).lastrowid

        user_4 = connection.execute(
            """
            INSERT INTO users (tenant_id, name, role)
            VALUES (?, ?, ?)
            """,
            ("tenant-2", "User Four", "member"),
        ).lastrowid

        connection.execute(
            """
            INSERT INTO service_acts (
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "tenant-2",
                user_3,
                user_4,
                "Tenant Two Service Act",
                "Tenant two test service act",
            ),
        )
        connection.commit()

        yield connection

    finally:
        connection.close()
