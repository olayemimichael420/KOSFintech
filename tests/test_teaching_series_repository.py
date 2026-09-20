import pytest

from models.teaching_series import TeachingSeries
from repositories.teaching_series_repository import TeachingSeriesRepository


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _create_session(connection, tenant_id, name, start_date, end_date):
    cursor = connection.execute(
        """
        INSERT INTO teaching_sessions (
            tenant_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (tenant_id, name, start_date, end_date),
    )
    connection.commit()
    return cursor.lastrowid


def test_session_exists(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    session_id = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    assert repository.session_exists("tenant-cmos", session_id)
    assert not repository.session_exists("other-tenant", session_id)


def test_create_persists_and_returns_series(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    session_id = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    series = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=session_id,
            name="Faith Series",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    assert series.id is not None
    assert repository.get("tenant-cmos", series.id) == series


def test_get_is_tenant_scoped(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    session_id = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    series = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=session_id,
            name="Kingdom Series",
            start_date="2026-03-01",
            end_date="2026-03-31",
        )
    )

    assert repository.get("tenant-cmos", series.id) == series
    assert repository.get("other-tenant", series.id) is None


def test_list_is_session_and_tenant_scoped_and_ordered(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    first_session = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )
    second_session = _create_session(
        connection,
        "tenant-cmos",
        "2027 Teaching",
        "2027-01-01",
        "2027-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    late = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=first_session,
            name="Second",
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    early = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=first_session,
            name="First",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    other_session = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=second_session,
            name="Other Session",
            start_date="2027-02-01",
            end_date="2027-02-28",
        )
    )

    assert repository.list("tenant-cmos", first_session) == [early, late]
    assert repository.list("tenant-cmos", first_session) != [other_session]


def test_duplicate_name_within_same_session_is_rejected(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    session_id = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=session_id,
            name="Faith Series",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    with pytest.raises(Exception):
        repository.create(
            TeachingSeries(
                id=None,
                tenant_id="tenant-cmos",
                teaching_session_id=session_id,
                name="Faith Series",
                start_date="2026-03-01",
                end_date="2026-03-31",
            )
        )


def test_same_name_is_allowed_in_different_sessions(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    first_session = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )
    second_session = _create_session(
        connection,
        "tenant-cmos",
        "2027 Teaching",
        "2027-01-01",
        "2027-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    first = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=first_session,
            name="Faith Series",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    second = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=second_session,
            name="Faith Series",
            start_date="2027-02-01",
            end_date="2027-02-28",
        )
    )

    assert first.id != second.id


def test_same_name_is_allowed_in_different_tenants(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    _create_tenant(connection, "tenant-other")
    first_session = _create_session(
        connection,
        "tenant-cmos",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )
    second_session = _create_session(
        connection,
        "tenant-other",
        "2026 Teaching",
        "2026-01-01",
        "2026-12-31",
    )

    repository = TeachingSeriesRepository(connection)

    first = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-cmos",
            teaching_session_id=first_session,
            name="Faith Series",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    second = repository.create(
        TeachingSeries(
            id=None,
            tenant_id="tenant-other",
            teaching_session_id=second_session,
            name="Faith Series",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    assert first.id != second.id


def test_unknown_session_is_rejected_by_database(db_connection):
    connection = db_connection
    _create_tenant(connection, "tenant-cmos")
    repository = TeachingSeriesRepository(connection)

    with pytest.raises(Exception):
        repository.create(
            TeachingSeries(
                id=None,
                tenant_id="tenant-cmos",
                teaching_session_id=999999,
                name="Orphan Series",
                start_date="2026-02-01",
                end_date="2026-02-28",
            )
        )
