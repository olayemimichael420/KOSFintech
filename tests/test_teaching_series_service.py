import sqlite3

import pytest

from models.teaching_series import TeachingSeries
from repositories.teaching_series_repository import TeachingSeriesRepository
from repositories.teaching_session_repository import TeachingSessionRepository
from services.teaching_series_service import TeachingSeriesService


def _create_service(tenant_id="tenant-1", connection=None):
    if connection is None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

        connection.execute(
            """
            CREATE TABLE teaching_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                UNIQUE (tenant_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX ux_teaching_sessions_id_tenant
            ON teaching_sessions(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE teaching_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                teaching_session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (teaching_session_id, tenant_id)
                    REFERENCES teaching_sessions(id, tenant_id),
                UNIQUE (tenant_id, teaching_session_id, name)
            )
            """
        )

        connection.commit()

    return (
        TeachingSeriesService(
            repository=TeachingSeriesRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
        ),
        connection,
    )


def _create_session(
    connection,
    tenant_id,
    start_date,
    end_date,
    name="2026 Teaching",
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


def _series(session_id, tenant_id="tenant-1",
            start_date="2026-02-01", end_date="2026-02-28"):
    return TeachingSeries(
        id=None,
        tenant_id=tenant_id,
        teaching_session_id=session_id,
        name="Faith Series",
        start_date=start_date,
        end_date=end_date,
    )


def test_create_rejects_tenant_mismatch():
    service, connection = _create_service()

    try:
        with pytest.raises(ValueError, match="tenant mismatch"):
            service.create(_series(1, tenant_id="tenant-2"))
    finally:
        connection.close()


def test_create_rejects_invalid_date_range():
    service, connection = _create_service()

    try:
        session_id = _create_session(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-12-31",
        )

        with pytest.raises(
            ValueError,
            match="start date must not be after end date",
        ):
            service.create(
                _series(
                    session_id,
                    start_date="2026-05-01",
                    end_date="2026-04-01",
                )
            )
    finally:
        connection.close()


def test_create_rejects_missing_session():
    service, connection = _create_service()

    try:
        with pytest.raises(
            ValueError,
            match="teaching session not found",
        ):
            service.create(_series(999999))
    finally:
        connection.close()


def test_create_rejects_series_start_before_session():
    service, connection = _create_service()

    try:
        session_id = _create_session(
            connection,
            "tenant-1",
            "2026-03-01",
            "2026-12-31",
        )

        with pytest.raises(
            ValueError,
            match="start date must be within teaching session",
        ):
            service.create(
                _series(
                    session_id,
                    start_date="2026-02-28",
                    end_date="2026-03-31",
                )
            )
    finally:
        connection.close()


def test_create_rejects_series_end_after_session():
    service, connection = _create_service()

    try:
        session_id = _create_session(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-10-31",
        )

        with pytest.raises(
            ValueError,
            match="end date must be within teaching session",
        ):
            service.create(
                _series(
                    session_id,
                    start_date="2026-10-01",
                    end_date="2026-11-01",
                )
            )
    finally:
        connection.close()


def test_create_accepts_series_within_session():
    service, connection = _create_service()

    try:
        session_id = _create_session(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-12-31",
        )

        series = service.create(_series(session_id))

        assert series.id is not None
        assert series.teaching_session_id == session_id
        assert series.tenant_id == "tenant-1"
    finally:
        connection.close()


def test_list_is_session_scoped():
    service, connection = _create_service()

    try:
        first_session = _create_session(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-06-30",
        )
        second_session = _create_session(
            connection,
            "tenant-1",
            "2026-07-01",
            "2026-12-31",
            name="2026 Teaching Part Two",
        )

        first = service.create(
            _series(
                first_session,
                start_date="2026-02-01",
                end_date="2026-02-28",
            )
        )
        service.create(
            _series(
                second_session,
                start_date="2026-08-01",
                end_date="2026-08-31",
            )
        )

        assert service.list(first_session) == [first]
    finally:
        connection.close()


def test_get_is_tenant_scoped():
    service, connection = _create_service()

    try:
        session_id = _create_session(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-12-31",
        )
        series = service.create(_series(session_id))

        other_service, _ = _create_service(
            tenant_id="tenant-2",
            connection=connection,
        )

        assert service.get(series.id) == series
        assert other_service.get(series.id) is None
    finally:
        connection.close()
