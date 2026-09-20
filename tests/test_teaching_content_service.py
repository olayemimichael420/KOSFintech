import pytest

from models.teaching_content import TeachingContent
from repositories.teaching_content_repository import TeachingContentRepository
from repositories.teaching_focus_repository import TeachingFocusRepository
from repositories.teaching_series_repository import TeachingSeriesRepository
from services.teaching_content_service import TeachingContentService


def _create_tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _create_session(connection, tenant_id):
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
        (
            tenant_id,
            "Teaching Session",
            "2026-01-01",
            "2026-12-31",
        ),
    )
    connection.commit()
    return cursor.lastrowid


def _create_series(connection, tenant_id, session_id):
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
            "Faith Series",
            "2026-01-01",
            "2026-12-31",
        ),
    )
    connection.commit()
    return cursor.lastrowid


def _create_focus(connection, tenant_id, series_id):
    cursor = connection.execute(
        """
        INSERT INTO teaching_focuses (
            tenant_id,
            teaching_series_id,
            name,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            series_id,
            "Faith Focus",
            "2026-02-01",
            "2026-03-31",
        ),
    )
    connection.commit()
    return cursor.lastrowid


def _create_service(connection, tenant_id):
    return TeachingContentService(
        repository=TeachingContentRepository(connection),
        tenant_id=tenant_id,
        connection=connection,
        focus_repository=TeachingFocusRepository(connection),
    )


def test_create_and_get(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    _create_tenant(connection, tenant_id)
    session_id = _create_session(connection, tenant_id)
    series_id = _create_series(connection, tenant_id, session_id)
    focus_id = _create_focus(connection, tenant_id, series_id)

    service = _create_service(connection, tenant_id)

    created = service.create(
        TeachingContent(
            id=None,
            tenant_id=tenant_id,
            teaching_focus_id=focus_id,
            name="Introduction",
            description="Opening teaching content",
            sequence=1,
        )
    )

    assert created.id is not None
    assert service.get(created.id) == created


def test_create_rejects_tenant_mismatch(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    _create_tenant(connection, tenant_id)
    session_id = _create_session(connection, tenant_id)
    series_id = _create_series(connection, tenant_id, session_id)
    focus_id = _create_focus(connection, tenant_id, series_id)

    service = _create_service(connection, tenant_id)

    with pytest.raises(
        ValueError,
        match="teaching content tenant mismatch",
    ):
        service.create(
            TeachingContent(
                id=None,
                tenant_id="tenant-other",
                teaching_focus_id=focus_id,
                name="Invalid Content",
            )
        )


def test_create_rejects_missing_focus(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    _create_tenant(connection, tenant_id)

    service = _create_service(connection, tenant_id)

    with pytest.raises(
        ValueError,
        match="teaching focus not found",
    ):
        service.create(
            TeachingContent(
                id=None,
                tenant_id=tenant_id,
                teaching_focus_id=999999,
                name="Invalid Content",
            )
        )


def test_list_is_focus_scoped_and_ordered(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    _create_tenant(connection, tenant_id)
    session_id = _create_session(connection, tenant_id)
    series_id = _create_series(connection, tenant_id, session_id)
    focus_id = _create_focus(connection, tenant_id, series_id)

    service = _create_service(connection, tenant_id)

    service.create(
        TeachingContent(
            id=None,
            tenant_id=tenant_id,
            teaching_focus_id=focus_id,
            name="Second",
            sequence=2,
        )
    )
    service.create(
        TeachingContent(
            id=None,
            tenant_id=tenant_id,
            teaching_focus_id=focus_id,
            name="First",
            sequence=1,
        )
    )

    assert [
        content.name for content in service.list(focus_id)
    ] == ["First", "Second"]


def test_list_missing_focus_returns_empty(db_connection):
    connection = db_connection
    tenant_id = "tenant-cmos"

    _create_tenant(connection, tenant_id)

    service = _create_service(connection, tenant_id)

    assert service.list(999999) == []
