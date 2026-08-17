import sqlite3

from models.school_admin import SchoolAdmin
from repositories.school_admin_repository import SchoolAdminRepository


def create_tables(connection):
    connection.execute(
        """
        CREATE TABLE schools (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            school_type TEXT NOT NULL,
            country TEXT NOT NULL,
            currency TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE school_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'admin1', 'admin2')),
            phone TEXT NOT NULL UNIQUE,
            email TEXT,
            verified BOOLEAN DEFAULT 0,
            verification_code TEXT,
            code_expires TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES schools(tenant_id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO schools (
            tenant_id,
            name,
            school_type,
            country,
            currency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "school-001",
            "KOS Community School",
            "Secondary",
            "Nigeria",
            "NGN",
        ),
    )

    connection.commit()


def test_create_get_and_list_school_admin():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    create_tables(connection)

    repository = SchoolAdminRepository(connection)

    admin = SchoolAdmin(
        id=None,
        tenant_id="school-001",
        user_id=1001,
        role="owner",
        phone="+2348000000000",
        email="admin@koscommunity.example",
        verified=True,
    )

    created = repository.create(admin)

    assert created.id is not None

    result = repository.get(created.id)

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.user_id == 1001
    assert result.role == "owner"
    assert result.phone == "+2348000000000"
    assert result.email == "admin@koscommunity.example"
    assert result.verified is True

    admins = repository.list_by_school("school-001")

    assert len(admins) == 1
    assert admins[0].id == created.id

    connection.close()
