import sqlite3
from datetime import datetime, timezone

import pytest

from database import init_db
from services.judicial_appointment_conferral_service import (
    JudicialAppointmentConferralService,
)


def make_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "j4.db"
    monkeypatch.setattr("database.get_db_path", lambda: str(db_path))
    init_db()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def seed_user(connection, user_id, tenant_id, status="active"):
    connection.execute(
        """
        INSERT INTO users (id, tenant_id, name, email, role, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            tenant_id,
            f"User {user_id}",
            f"user{user_id}@example.com",
            "member",
            status,
        ),
    )


def seed_jurisdiction(connection, jurisdiction_id, tenant_id, status="active"):
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
            jurisdiction_id,
            tenant_id,
            "resource",
            "test jurisdiction",
            "local",
            "test",
            status,
        ),
    )


def seed_appointment(
    connection,
    appointment_id,
    tenant_id,
    candidate_user_id,
    jurisdiction_id,
    appointed_by,
    status="appointed",
):
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
            appointment_id,
            tenant_id,
            candidate_user_id,
            jurisdiction_id,
            "local",
            "test appointment",
            "test constitutional basis",
            "test qualification record",
            appointed_by,
            status,
        ),
    )


def seed_proposed_authority(
    connection,
    authority_id,
    tenant_id,
    user_id,
    jurisdiction_id,
    appointment_id,
):
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
            authority_id,
            tenant_id,
            user_id,
            "judicial",
            jurisdiction_id,
            "local",
            appointment_id,
            0,
            "proposed",
        ),
    )


def test_create_appointment_requires_active_candidate(tmp_path, monkeypatch):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001", status="inactive")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="candidate user is inactive"):
        service.create_appointment(
            candidate_user_id=1,
            jurisdiction_id=1,
            judicial_level="local",
            appointment_source="constitutional appointment",
            appointment_basis="approved basis",
            qualification_record="qualified",
            appointed_by=2,
        )


def test_create_appointment_requires_active_appointing_user(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001", status="inactive")
    seed_jurisdiction(connection, 1, "tenant-001")

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="appointing user is inactive"):
        service.create_appointment(
            candidate_user_id=1,
            jurisdiction_id=1,
            judicial_level="local",
            appointment_source="constitutional appointment",
            appointment_basis="approved basis",
            qualification_record="qualified",
            appointed_by=2,
        )


def test_create_appointment_requires_same_tenant(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-002")
    seed_jurisdiction(connection, 1, "tenant-001")

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="tenant mismatch"):
        service.create_appointment(
            candidate_user_id=1,
            jurisdiction_id=1,
            judicial_level="local",
            appointment_source="constitutional appointment",
            appointment_basis="approved basis",
            qualification_record="qualified",
            appointed_by=2,
        )


def test_create_appointment_requires_active_jurisdiction(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001", status="inactive")

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="judicial jurisdiction is inactive"):
        service.create_appointment(
            candidate_user_id=1,
            jurisdiction_id=1,
            judicial_level="local",
            appointment_source="constitutional appointment",
            appointment_basis="approved basis",
            qualification_record="qualified",
            appointed_by=2,
        )


def test_create_appointment_records_provenance_without_activation(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")

    service = JudicialAppointmentConferralService(connection)

    appointment = service.create_appointment(
        candidate_user_id=1,
        jurisdiction_id=1,
        judicial_level="local",
        appointment_source="constitutional appointment",
        appointment_basis="approved basis",
        qualification_record="qualification verified",
        appointed_by=2,
    )

    assert appointment.id is not None
    assert appointment.status == "appointed"

    authority = connection.execute(
        """
        SELECT id
        FROM judicial_authorities
        WHERE tenant_id = 'tenant-001'
        """
    ).fetchone()

    assert authority is None


def test_create_proposed_authority_requires_appointment(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="judicial appointment not found"):
        service.create_proposed_authority(
            appointment_id=999,
            authority_type="judicial",
        )


def test_create_proposed_authority_preserves_appointment_provenance(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")
    seed_appointment(
        connection,
        1,
        "tenant-001",
        1,
        1,
        2,
    )
    connection.commit()

    service = JudicialAppointmentConferralService(connection)

    authority = service.create_proposed_authority(
        appointment_id=1,
        authority_type="judicial",
    )

    assert authority.id is not None
    assert authority.user_id == 1
    assert authority.jurisdiction_id == 1
    assert authority.appointment_id == 1
    assert authority.status.value == "proposed"


def test_create_conferral_requires_proposed_authority(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")
    seed_appointment(
        connection,
        1,
        "tenant-001",
        1,
        1,
        2,
    )
    connection.commit()

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="judicial authority not found"):
        service.create_conferral(
            appointment_id=1,
            authority_id=999,
            conferring_authority="constitutional authority",
            conferral_instrument="instrument-001",
        )


def test_create_conferral_records_instrument_and_effective_window(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")
    seed_appointment(
        connection,
        1,
        "tenant-001",
        1,
        1,
        2,
    )
    seed_proposed_authority(
        connection,
        1,
        "tenant-001",
        1,
        1,
        1,
    )
    connection.commit()

    service = JudicialAppointmentConferralService(connection)

    conferral = service.create_conferral(
        appointment_id=1,
        authority_id=1,
        conferring_authority="constitutional authority",
        conferral_instrument="instrument-001",
        effective_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        effective_until=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )

    assert conferral.id is not None
    assert conferral.appointment_id == 1
    assert conferral.authority_id == 1
    assert conferral.conferring_authority == "constitutional authority"
    assert conferral.conferral_instrument == "instrument-001"


def test_activate_authority_requires_valid_provenance_chain(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")
    seed_appointment(
        connection,
        1,
        "tenant-001",
        1,
        1,
        2,
    )
    seed_proposed_authority(
        connection,
        1,
        "tenant-001",
        1,
        1,
        1,
    )
    connection.commit()

    service = JudicialAppointmentConferralService(connection)

    with pytest.raises(ValueError, match="judicial conferral not found"):
        service.activate_authority(
            authority_id=1,
            now=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

    status = connection.execute(
        """
        SELECT status
        FROM judicial_authorities
        WHERE id = 1
        """
    ).fetchone()["status"]

    assert status == "proposed"


def test_activate_authority_requires_coherent_provenance(
    tmp_path, monkeypatch
):
    connection = make_connection(tmp_path, monkeypatch)
    seed_user(connection, 1, "tenant-001")
    seed_user(connection, 2, "tenant-001")
    seed_jurisdiction(connection, 1, "tenant-001")
    seed_appointment(
        connection,
        1,
        "tenant-001",
        1,
        1,
        2,
    )
    seed_proposed_authority(
        connection,
        1,
        "tenant-001",
        1,
        1,
        1,
    )

    connection.execute(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument
        )
        VALUES (1, 'tenant-001', 1, 1, 'authority', 'instrument')
        """
    )
    connection.commit()

    service = JudicialAppointmentConferralService(connection)

    authority = service.activate_authority(
        authority_id=1,
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert authority.status.value == "active"

    stored = connection.execute(
        """
        SELECT status, appointment_id, jurisdiction_id
        FROM judicial_authorities
        WHERE id = 1
        """
    ).fetchone()

    assert stored["status"] == "active"
    assert stored["appointment_id"] == 1
    assert stored["jurisdiction_id"] == 1
