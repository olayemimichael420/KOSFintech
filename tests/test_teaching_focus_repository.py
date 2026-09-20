import pytest

from models.teaching_focus import TeachingFocus
from repositories.teaching_focus_repository import TeachingFocusRepository


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _create_session(
    connection,
    tenant_id,
    name="2026 Teaching",
    start_date="2026-01-01",
    end_date="2026-12-31",
):
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


def _create_series(
    connection,
    tenant_id,
    session_id,
    name="Faith Series",
    start_date="2026-02-01",
    end_date="2026-06-30",
):
    cursor = connection.execute(
        """
        INSERT INTO teaching_series (
            tenant_id,
            teaching_session_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            session_id,
            name,
            start_date,
            end_date,
        ),
    )
    connection.commit()
    return cursor.lastrowid


@pytest.fixture
def repository_context(db_connection):
    tenant_a = "teaching-focus-a"
    tenant_b = "teaching-focus-b"

    connection = db_connection

    _create_tenant(connection, tenant_a)
    _create_tenant(connection, tenant_b)

    session_a = _create_session(connection, tenant_a)
    series_a = _create_series(
        connection,
        tenant_a,
        session_a,
    )

    return connection, tenant_a, tenant_b, session_a, series_a


def test_series_exists(repository_context):
    connection, tenant_a, _tenant_b, _session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    assert repository.series_exists(tenant_a, series_id) is True
    assert repository.series_exists(tenant_a, 999999) is False


def test_create_persists_and_returns_focus(repository_context):
    connection, tenant_a, _tenant_b, _session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    focus = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    assert focus.id is not None
    assert repository.get(tenant_a, focus.id) == focus


def test_get_is_tenant_scoped(repository_context):
    connection, tenant_a, tenant_b, _session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    focus = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    assert repository.get(tenant_a, focus.id) == focus
    assert repository.get(tenant_b, focus.id) is None


def test_list_is_series_and_tenant_scoped_and_ordered(
    repository_context,
):
    connection, tenant_a, tenant_b, session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    later = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Hope",
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    earlier = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    other_session = _create_session(
        connection,
        tenant_a,
        name="2027 Teaching",
        start_date="2027-01-01",
        end_date="2027-12-31",
    )
    other_series = _create_series(
        connection,
        tenant_a,
        other_session,
        name="Other Series",
        start_date="2027-02-01",
        end_date="2027-06-30",
    )

    repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=other_series,
            name="Other",
            start_date="2027-02-01",
            end_date="2027-02-28",
        )
    )

    assert repository.list(tenant_a, series_id) == [earlier, later]
    assert repository.list(tenant_b, series_id) == []


def test_duplicate_name_within_same_series_is_rejected(
    repository_context,
):
    connection, tenant_a, _tenant_b, _session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    focus = TeachingFocus(
        id=None,
        tenant_id=tenant_a,
        teaching_series_id=series_id,
        name="Faith",
        start_date="2026-02-01",
        end_date="2026-02-28",
    )

    repository.create(focus)

    with pytest.raises(Exception):
        repository.create(focus)


def test_same_name_is_allowed_in_different_series(
    repository_context,
):
    connection, tenant_a, _tenant_b, session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    other_session = _create_session(
        connection,
        tenant_a,
        name="2027 Teaching",
        start_date="2027-01-01",
        end_date="2027-12-31",
    )
    other_series = _create_series(
        connection,
        tenant_a,
        other_session,
        name="Hope Series",
        start_date="2027-02-01",
        end_date="2027-06-30",
    )

    first = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    second = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=other_series,
            name="Faith",
            start_date="2027-02-01",
            end_date="2027-02-28",
        )
    )

    assert first.name == second.name
    assert first.id != second.id


def test_same_name_is_allowed_in_different_tenants(
    repository_context,
):
    connection, tenant_a, tenant_b, _session_id, series_id = (
        repository_context
    )

    repository = TeachingFocusRepository(connection)

    tenant_b_session = _create_session(
        connection,
        tenant_b,
        name="2026 Teaching B",
    )
    tenant_b_series = _create_series(
        connection,
        tenant_b,
        tenant_b_session,
        name="Faith Series B",
    )

    first = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_a,
            teaching_series_id=series_id,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    second = repository.create(
        TeachingFocus(
            id=None,
            tenant_id=tenant_b,
            teaching_series_id=tenant_b_series,
            name="Faith",
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
    )

    assert first.name == second.name
    assert first.id != second.id
