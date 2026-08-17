import sqlite3

from models.school import School
from repositories.school_repository import SchoolRepository


def test_create_and_get_school():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

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

    repository = SchoolRepository(connection)

    school = School(
        tenant_id="school-001",
        name="KOS Community School",
        school_type="Secondary",
        country="Nigeria",
        currency="NGN",
    )

    repository.create(school)

    result = repository.get("school-001")

    assert result is not None
    assert result.tenant_id == "school-001"
    assert result.name == "KOS Community School"
    assert result.school_type == "Secondary"
    assert result.country == "Nigeria"
    assert result.currency == "NGN"

    connection.close()
