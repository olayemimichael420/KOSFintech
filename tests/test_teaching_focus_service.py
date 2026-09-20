import sqlite3

import pytest

from models.teaching_focus import TeachingFocus
from repositories.teaching_focus_repository import TeachingFocusRepository
from repositories.teaching_series_repository import TeachingSeriesRepository
from services.teaching_focus_service import TeachingFocusService


def _create_service(tenant_id="tenant-1", connection=None):
    if connection is None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

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
                UNIQUE (tenant_id, teaching_session_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX ux_teaching_series_id_tenant
            ON teaching_series(id, tenant_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE teaching_focuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                teaching_series_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (tenant_id)
                    REFERENCES teaching_series(tenant_id),
                FOREIGN KEY (teaching_series_id, tenant_id)
                    REFERENCES teaching_series(id, tenant_id),
                UNIQUE (tenant_id, teaching_series_id, name)
            )
            """
        )

        connection.commit()

    return (
        TeachingFocusService(
            repository=TeachingFocusRepository(connection),
            tenant_id=tenant_id,
            connection=connection,
            series_repository=TeachingSeriesRepository(connection),
        ),
        connection,
    )


def _create_series(
    connection,
    tenant_id,
    start_date,
    end_date,
    name="Faith Series",
    session_id=1,
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


def _focus(
    series_id,
    tenant_id="tenant-1",
    start_date="2026-02-01",
    end_date="2026-02-28",
):
    return TeachingFocus(
        id=None,
        tenant_id=tenant_id,
        teaching_series_id=series_id,
        name="Faith",
        start_date=start_date,
        end_date=end_date,
    )


def test_create_rejects_tenant_mismatch():
    service, connection = _create_service()

    try:
        with pytest.raises(ValueError, match="tenant mismatch"):
            service.create(_focus(1, tenant_id="tenant-2"))
    finally:
        connection.close()


def test_create_rejects_invalid_date_range():
    service, connection = _create_service()

    try:
        series_id = _create_series(
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
                _focus(
                    series_id,
                    start_date="2026-05-01",
                    end_date="2026-04-01",
                )
            )
    finally:
        connection.close()


def test_create_rejects_missing_series():
    service, connection = _create_service()

    try:
        with pytest.raises(
            ValueError,
            match="teaching series not found",
        ):
            service.create(_focus(999999))
    finally:
        connection.close()


def test_create_rejects_focus_start_before_series():
    service, connection = _create_service()

    try:
        series_id = _create_series(
            connection,
            "tenant-1",
            "2026-03-01",
            "2026-12-31",
        )

        with pytest.raises(
            ValueError,
            match="start date must be within teaching series",
        ):
            service.create(
                _focus(
                    series_id,
                    start_date="2026-02-28",
                    end_date="2026-03-31",
                )
            )
    finally:
        connection.close()


def test_create_rejects_focus_end_after_series():
    service, connection = _create_service()

    try:
        series_id = _create_series(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-10-31",
        )

        with pytest.raises(
            ValueError,
            match="end date must be within teaching series",
        ):
            service.create(
                _focus(
                    series_id,
                    start_date="2026-10-01",
                    end_date="2026-11-01",
                )
            )
    finally:
        connection.close()


def test_create_accepts_focus_within_series():
    service, connection = _create_service()

    try:
        series_id = _create_series(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-12-31",
        )

        focus = service.create(_focus(series_id))

        assert focus.id is not None
        assert focus.teaching_series_id == series_id
        assert focus.tenant_id == "tenant-1"
    finally:
        connection.close()


def test_list_is_series_scoped():
    service, connection = _create_service()

    try:
        first_series = _create_series(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-06-30",
            name="First Series",
        )
        second_series = _create_series(
            connection,
            "tenant-1",
            "2026-07-01",
            "2026-12-31",
            name="Second Series",
        )

        first = service.create(
            _focus(
                first_series,
                start_date="2026-02-01",
                end_date="2026-02-28",
            )
        )

        service.create(
            _focus(
                second_series,
                start_date="2026-08-01",
                end_date="2026-08-31",
            )
        )

        assert service.list(first_series) == [first]
    finally:
        connection.close()


def test_get_is_tenant_scoped():
    service, connection = _create_service()

    try:
        series_id = _create_series(
            connection,
            "tenant-1",
            "2026-01-01",
            "2026-12-31",
        )

        focus = service.create(_focus(series_id))

        other_service, _ = _create_service(
            tenant_id="tenant-2",
            connection=connection,
        )

        assert service.get(focus.id) == focus
        assert other_service.get(focus.id) is None
    finally:
        connection.close()
