import sqlite3
from datetime import datetime, timedelta, timezone

import database
from services.judicial_authorization_service import JudicialAuthorizationService


def seed_judicial_authority(
    connection,
    *,
    tenant_id="tenant-001",
    user_id=1,
    jurisdiction_id=1,
    status="active",
    effective_from=None,
    effective_until=None,
):
    connection.execute(
        """
        INSERT INTO judicial_authorities (
            tenant_id,
            user_id,
            authority_type,
            jurisdiction_id,
            judicial_level,
            appointment_id,
            conferral_id,
            status,
            effective_from,
            effective_until
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            user_id,
            "first_instance_judicial",
            jurisdiction_id,
            "first_instance",
            1,
            1,
            status,
            effective_from,
            effective_until,
        ),
    )


def build_database(tmp_path, monkeypatch):
    db_path = tmp_path / "judicial_authorization.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()
    connection = database.get_connection()

    connection.execute(
        """
        INSERT INTO users (tenant_id, name, role, status)
        VALUES (?, ?, ?, ?)
        """,
        ("tenant-001", "Judge One", "member", "active"),
    )

    connection.execute(
        """
        INSERT INTO judicial_jurisdictions (
            tenant_id,
            jurisdiction_type,
            jurisdiction_scope,
            judicial_level,
            case_types,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-001",
            "school",
            "school-001",
            "first_instance",
            "service_act",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_appointments (
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tenant-001",
            1,
            1,
            "first_instance",
            "test_appointment",
            "test_basis",
            "test_qualification",
            1,
            "appointed",
        ),
    )

    connection.commit()
    return connection


def test_active_judicial_authority_is_authorized(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        seed_judicial_authority(connection)
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
        )

        assert decision.allowed is True
        assert decision.reason == "active judicial authority authorized"
        assert service.authorize(
            user_id=1,
            jurisdiction_id=1,
        ) is True
    finally:
        connection.close()


def test_missing_judicial_authority_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
        )

        assert decision.allowed is False
        assert decision.reason == "no active judicial authority"
    finally:
        connection.close()


def test_inactive_judicial_authority_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        seed_judicial_authority(connection, status="suspended")
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
        )

        assert decision.allowed is False
        assert decision.reason == "no active judicial authority"
    finally:
        connection.close()


def test_inactive_user_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            "UPDATE users SET status = 'inactive' WHERE id = 1"
        )
        seed_judicial_authority(connection)
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
        )

        assert decision.allowed is False
        assert decision.reason == "authenticated user is inactive"
    finally:
        connection.close()


def test_inactive_jurisdiction_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            UPDATE judicial_jurisdictions
            SET status = 'inactive'
            WHERE id = 1
            """
        )
        seed_judicial_authority(connection)
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
        )

        assert decision.allowed is False
        assert decision.reason == "judicial jurisdiction is inactive"
    finally:
        connection.close()


def test_wrong_jurisdiction_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            INSERT INTO judicial_jurisdictions (
                tenant_id,
                jurisdiction_type,
                jurisdiction_scope,
                judicial_level,
                case_types,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                "school",
                "school-002",
                "first_instance",
                "service_act",
                "active",
            ),
        )
        seed_judicial_authority(connection, jurisdiction_id=1)
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=2,
        )

        assert decision.allowed is False
        assert decision.reason == "judicial authority jurisdiction mismatch"
    finally:
        connection.close()


def test_future_authority_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        now = datetime.now(timezone.utc)
        seed_judicial_authority(
            connection,
            effective_from=(now + timedelta(days=1)).isoformat(),
        )
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
            now=now,
        )

        assert decision.allowed is False
        assert decision.reason == "judicial authority is not yet effective"
    finally:
        connection.close()


def test_expired_authority_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        now = datetime.now(timezone.utc)
        seed_judicial_authority(
            connection,
            effective_until=(now - timedelta(days=1)).isoformat(),
        )
        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=1,
            now=now,
        )

        assert decision.allowed is False
        assert decision.reason == "judicial authority has expired"
    finally:
        connection.close()


def test_unknown_user_is_denied(tmp_path, monkeypatch):
    connection = build_database(tmp_path, monkeypatch)

    try:
        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=999999,
            jurisdiction_id=1,
        )

        assert decision.allowed is False
        assert decision.reason == "authenticated user not found"
    finally:
        connection.close()


def test_matching_active_authority_is_found_when_multiple_authorities_exist(
    tmp_path,
    monkeypatch,
):
    connection = build_database(tmp_path, monkeypatch)

    try:
        connection.execute(
            """
            INSERT INTO judicial_jurisdictions (
                tenant_id,
                jurisdiction_type,
                jurisdiction_scope,
                judicial_level,
                case_types,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                "school",
                "school-002",
                "first_instance",
                "service_act",
                "active",
            ),
        )

        connection.execute(
            """
            INSERT INTO judicial_appointments (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                1,
                2,
                "first_instance",
                "test_appointment",
                "test_basis",
                "test_qualification",
                1,
                "appointed",
            ),
        )

        seed_judicial_authority(
            connection,
            jurisdiction_id=2,
        )

        connection.execute(
            """
            INSERT INTO judicial_appointments (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tenant-001",
                1,
                1,
                "first_instance",
                "test_appointment_latest",
                "test_basis",
                "test_qualification",
                1,
                "appointed",
            ),
        )

        seed_judicial_authority(
            connection,
            jurisdiction_id=1,
        )

        connection.commit()

        service = JudicialAuthorizationService(connection)

        decision = service.authorize_decision(
            user_id=1,
            jurisdiction_id=2,
        )

        assert decision.allowed is True
        assert decision.reason == "active judicial authority authorized"
    finally:
        connection.close()
