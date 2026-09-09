import sqlite3
import database
import pytest
from database import init_db


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


@pytest.fixture
def setup_j5d(tmp_path):
    db_path = tmp_path / "j5d.db"
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    import config

    original_db_file = config.settings.db_file

    object.__setattr__(
        config.settings,
        "db_file",
        db_path,
    )

    try:
        init_db()
    finally:
        object.__setattr__(
            config.settings,
            "db_file",
            original_db_file,
        )

    connection.close()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executemany(
        """
        INSERT INTO users (
            id,
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "tenant-001", "Judge", "judge@example.com", "member", "active"),
            (2, "tenant-001", "Other", "other@example.com", "member", "active"),
            (3, "tenant-002", "Other Tenant", "other2@example.com", "member", "active"),
            (4, "tenant-002", "Other Tenant Two", "other3@example.com", "member", "active"),
        ],
    )

    connection.execute(
        """
        INSERT INTO judicial_jurisdictions (
            id,
            tenant_id,
            jurisdiction_type,
            jurisdiction_scope,
            judicial_level,
            case_types,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            "service",
            "tenant-001",
            "primary",
            "service_dispute",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_jurisdictions (
            id,
            tenant_id,
            jurisdiction_type,
            jurisdiction_scope,
            judicial_level,
            case_types,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            2,
            "tenant-002",
            "service",
            "tenant-002",
            "primary",
            "service_dispute",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_appointments (
            id,
            tenant_id,
            candidate_user_id,
            jurisdiction_id,
            judicial_level,
            appointment_source,
            appointment_basis,
            qualification_record,
            appointed_by,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "primary",
            "test-source",
            "test-basis",
            "qualified",
            2,
            "appointed",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_authorities (
            id,
            tenant_id,
            user_id,
            authority_type,
            jurisdiction_id,
            judicial_level,
            appointment_id,
            conferral_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            "judge",
            1,
            "primary",
            1,
            1,
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "test-conferring-authority",
            "test-instrument",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO service_acts (
            id,
            tenant_id,
            provider_user_id,
            recipient_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "Test service act",
            "Test description",
            "created",
        ),
    )

    connection.execute(
        """
        INSERT INTO disputes (
            id,
            tenant_id,
            service_act_id,
            initiator_user_id,
            initiator_role,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "recipient",
            "Test dispute",
            "open",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_proceedings (
            id,
            tenant_id,
            dispute_id,
            jurisdiction_id,
            proceeding_type,
            status,
            opened_by_authority_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "service_dispute",
            "active",
            1,
        ),
    )

    connection.commit()
    return connection
