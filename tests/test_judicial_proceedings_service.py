import sqlite3

import pytest

import database
from services.judicial_proceedings_service import JudicialProceedingsService


def make_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "j5c.db"

    monkeypatch.setattr(
        database,
        "get_db_path",
        lambda: str(db_path),
    )

    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def seed_valid_chain(connection):
    connection.execute(
        """
        INSERT INTO users
            (id, tenant_id, name, email, role, status)
        VALUES
            (1, 'tenant-001', 'Judge', 'judge@example.com', 'member', 'active'),
            (2, 'tenant-001', 'Admin', 'admin@example.com', 'member', 'active')
        """
    )

    connection.execute(
        """
        INSERT INTO judicial_jurisdictions
            (
                id,
                tenant_id,
                jurisdiction_type,
                jurisdiction_scope,
                judicial_level,
                case_types,
                status
            )
        VALUES
            (
                1,
                'tenant-001',
                'resource',
                'school-001',
                'local',
                'service_act',
                'active'
            )
        """
    )

    connection.execute(
        """
        INSERT INTO judicial_appointments
            (
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
        VALUES
            (
                1,
                'tenant-001',
                1,
                1,
                'local',
                'test appointment',
                'test basis',
                'test qualification',
                2,
                'appointed'
            )
        """
    )

    connection.execute(
        """
        INSERT INTO judicial_authorities
            (
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
        VALUES
            (
                1,
                'tenant-001',
                1,
                'judicial',
                1,
                'local',
                1,
                1,
                'active'
            )
        """
    )

    connection.execute(
        """
        INSERT INTO service_acts
            (
                id,
                tenant_id,
                provider_user_id,
                recipient_user_id,
                title,
                description,
                status
            )
        VALUES
            (
                1,
                'tenant-001',
                1,
                2,
                'Test service act',
                'Test service act description',
                'completed'
            )
        """
    )

    connection.execute(
        """
        INSERT INTO disputes
            (
                id,
                tenant_id,
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status
            )
        VALUES
            (
                1,
                'tenant-001',
                1,
                1,
                'provider',
                'Test dispute',
                'open'
            )
        """
    )

    connection.commit()


def build_database(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    seed_valid_chain(connection)
    return connection


def test_create_starts_proposed(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        assert proceeding.status.value == "proposed"
        assert proceeding.opened_by_authority_id == 1
    finally:
        connection.close()


def test_create_requires_active_authority(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            UPDATE judicial_authorities
            SET status = 'suspended'
            WHERE id = 1
            """
        )
        connection.commit()

        service = JudicialProceedingsService(connection)

        with pytest.raises(
            ValueError,
            match="no active judicial authority",
        ):
            service.create_proceeding(
                user_id=1,
                dispute_id=1,
                jurisdiction_id=1,
                proceeding_type="service_dispute",
            )
    finally:
        connection.close()


def test_create_requires_active_jurisdiction(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            UPDATE judicial_jurisdictions
            SET status = 'inactive'
            WHERE id = 1
            """
        )
        connection.commit()

        service = JudicialProceedingsService(connection)

        with pytest.raises(
            ValueError,
            match="judicial jurisdiction is inactive",
        ):
            service.create_proceeding(
                user_id=1,
                dispute_id=1,
                jurisdiction_id=1,
                proceeding_type="service_dispute",
            )
    finally:
        connection.close()


def test_create_requires_existing_dispute(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        with pytest.raises(
            ValueError,
            match="judicial dispute not found",
        ):
            service.create_proceeding(
                user_id=1,
                dispute_id=999,
                jurisdiction_id=1,
                proceeding_type="service_dispute",
            )
    finally:
        connection.close()


def test_create_requires_proceeding_type(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        with pytest.raises(
            ValueError,
            match="proceeding type is required",
        ):
            service.create_proceeding(
                user_id=1,
                dispute_id=1,
                jurisdiction_id=1,
                proceeding_type=" ",
            )
    finally:
        connection.close()


def test_lifecycle_proposed_open_active(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        opened = service.open_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        assert opened.status.value == "open"
        assert opened.opened_at is not None

        active = service.activate_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        assert active.status.value == "active"
    finally:
        connection.close()


def test_close_records_reason_and_timestamp(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        service.open_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        service.activate_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        closed = service.close_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
            closure_reason="Matter concluded.",
        )

        assert closed.status.value == "closed"
        assert closed.closed_at is not None
        assert closed.closure_reason == "Matter concluded."
    finally:
        connection.close()


@pytest.mark.parametrize(
    "status",
    ["proposed", "open", "active"],
)
def test_termination_records_reason_and_timestamp(
    tmp_path,
    monkeypatch,
    status,
):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        if status in ("open", "active"):
            service.open_proceeding(
                user_id=1,
                proceeding_id=proceeding.id,
            )

        if status == "active":
            service.activate_proceeding(
                user_id=1,
                proceeding_id=proceeding.id,
            )

        terminated = service.terminate_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
            termination_reason="Proceeding terminated.",
        )

        assert terminated.status.value == "terminated"
        assert terminated.closed_at is not None
        assert terminated.closure_reason == "Proceeding terminated."
    finally:
        connection.close()


def test_termination_requires_reason(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        with pytest.raises(
            ValueError,
            match="termination reason is required",
        ):
            service.terminate_proceeding(
                user_id=1,
                proceeding_id=proceeding.id,
                termination_reason=" ",
            )
    finally:
        connection.close()


def test_successful_operations_emit_audit_events(
    tmp_path,
    monkeypatch,
):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        service.open_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        service.activate_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        service.close_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
            closure_reason="Closed.",
        )

        events = connection.execute(
            """
            SELECT event_type
            FROM audit_events
            WHERE tenant_id = 'tenant-001'
            ORDER BY id
            """
        ).fetchall()

        event_types = [row["event_type"] for row in events]

        assert "judicial_proceeding_created" in event_types
        assert "judicial_proceeding_opened" in event_types
        assert "judicial_proceeding_activated" in event_types
        assert "judicial_proceeding_closed" in event_types
    finally:
        connection.close()


def test_proceeding_does_not_mutate_dispute(
    tmp_path,
    monkeypatch,
):
    connection = build_database(tmp_path, monkeypatch)

    try:
        before = connection.execute(
            """
            SELECT
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status
            FROM disputes
            WHERE id = 1
            """
        ).fetchone()

        service = JudicialProceedingsService(connection)

        proceeding = service.create_proceeding(
            user_id=1,
            dispute_id=1,
            jurisdiction_id=1,
            proceeding_type="service_dispute",
        )

        service.open_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        service.activate_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
        )

        service.close_proceeding(
            user_id=1,
            proceeding_id=proceeding.id,
            closure_reason="Closed.",
        )

        after = connection.execute(
            """
            SELECT
                service_act_id,
                initiator_user_id,
                initiator_role,
                reason,
                status
            FROM disputes
            WHERE id = 1
            """
        ).fetchone()

        assert tuple(before) == tuple(after)
    finally:
        connection.close()
