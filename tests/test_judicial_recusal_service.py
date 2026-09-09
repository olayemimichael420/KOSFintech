import sqlite3

import pytest

from database import init_db
from models.judicial_recusal import (
    JudicialRecusalScope,
    JudicialRecusalStatus,
)
from services.judicial_recusal_service import JudicialRecusalService


@pytest.fixture
def setup_j6c(tmp_path):
    db_path = tmp_path / "j6c.db"

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    import config

    original_db_file = config.settings.db_file

    object.__setattr__(
        config.settings,
        "db_file",
        db_path,
    )

    try:
        init_db()
    finally:
        object.__setattr__(
            config.settings,
            "db_file",
            original_db_file,
        )

    connection.close()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executemany(
        """
        INSERT INTO users (
            id,
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "tenant-001", "Judge", "judge@example.com", "member", "active"),
            (2, "tenant-001", "Other", "other@example.com", "member", "active"),
            (3, "tenant-002", "Other Tenant", "other2@example.com", "member", "active"),
            (4, "tenant-002", "Other Tenant Two", "other3@example.com", "member", "active"),
        ],
    )

    connection.executemany(
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
        [
            (
                1,
                "tenant-001",
                "service",
                "tenant-001",
                "primary",
                "service_dispute",
                "active",
            ),
            (
                2,
                "tenant-002",
                "service",
                "tenant-002",
                "primary",
                "service_dispute",
                "active",
            ),
        ],
    )

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
            1,
            "tenant-001",
            1,
            1,
            "primary",
            "test-source",
            "test-basis",
            "qualified",
            2,
            "appointed",
        ),
    )

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
            1,
            "tenant-001",
            1,
            "judge",
            1,
            "primary",
            1,
            1,
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "test-conferring-authority",
            "test-instrument",
            "active",
        ),
    )

    connection.execute(
        """
        INSERT INTO service_acts (
            id,
            tenant_id,
            provider_user_id,
            recipient_user_id,
            title,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "Test service act",
            "Test description",
            "created",
        ),
    )

    connection.execute(
        """
        INSERT INTO disputes (
            id,
            tenant_id,
            service_act_id,
            initiator_user_id,
            initiator_role,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            2,
            "recipient",
            "Test dispute",
            "open",
        ),
    )

    connection.execute(
        """
        INSERT INTO judicial_proceedings (
            id,
            tenant_id,
            dispute_id,
            jurisdiction_id,
            proceeding_type,
            status,
            opened_by_authority_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "tenant-001",
            1,
            1,
            "service_dispute",
            "active",
            1,
        ),
    )

    connection.commit()
    return connection


def test_record_jurisdiction_recusal_success(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Potential conflict of interest",
    )

    assert recusal.id is not None
    assert recusal.tenant_id == "tenant-001"
    assert recusal.judicial_authority_id == 1
    assert recusal.jurisdiction_id == 1
    assert recusal.proceeding_id is None
    assert recusal.scope == JudicialRecusalScope.JURISDICTION
    assert recusal.reason == "Potential conflict of interest"
    assert recusal.initiated_by == 1
    assert recusal.recorded_at is not None
    assert recusal.resolved_at is None
    assert recusal.status == JudicialRecusalStatus.ACTIVE


def test_record_proceeding_recusal_success(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.PROCEEDING,
        proceeding_id=1,
        reason="Proceeding-specific conflict",
    )

    assert recusal.scope == JudicialRecusalScope.PROCEEDING
    assert recusal.proceeding_id == 1
    assert recusal.status == JudicialRecusalStatus.ACTIVE


def test_record_recusal_requires_reason(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(ValueError, match="recusal reason is required"):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.JURISDICTION,
            reason="   ",
        )


def test_record_recusal_rejects_invalid_scope(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(ValueError, match="invalid judicial recusal scope"):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope="invalid",
            reason="Test reason",
        )


def test_jurisdiction_recusal_cannot_specify_proceeding(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(
        ValueError,
        match="jurisdiction recusal cannot specify a proceeding",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.JURISDICTION,
            proceeding_id=1,
            reason="Test reason",
        )


def test_proceeding_recusal_requires_proceeding(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(
        ValueError,
        match="proceeding recusal requires a proceeding",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.PROCEEDING,
            reason="Test reason",
        )


def test_record_recusal_requires_matching_active_authority(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(ValueError, match="judicial authority is inactive"):
        setup_j6c.execute(
            """
            UPDATE judicial_authorities
            SET status = 'inactive'
            WHERE id = 1
            """
        )
        setup_j6c.commit()

        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.JURISDICTION,
            reason="Test reason",
        )


def test_resolve_recusal_success(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Test reason",
    )

    resolved = service.resolve_recusal(
        user_id=1,
        recusal_id=recusal.id,
    )

    assert resolved.id == recusal.id
    assert resolved.status == JudicialRecusalStatus.RESOLVED
    assert resolved.resolved_at is not None
    assert resolved.reason == recusal.reason
    assert resolved.initiated_by == recusal.initiated_by
    assert resolved.recorded_at == recusal.recorded_at


def test_resolve_recusal_requires_active_recusal(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Test reason",
    )

    service.resolve_recusal(
        user_id=1,
        recusal_id=recusal.id,
    )

    with pytest.raises(
        ValueError,
        match="only active judicial recusals can be resolved",
    ):
        service.resolve_recusal(
            user_id=1,
            recusal_id=recusal.id,
        )


def test_resolve_recusal_is_tenant_scoped(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Test reason",
    )

    with pytest.raises(ValueError, match="no active judicial authority"):
        service.resolve_recusal(
            user_id=3,
            recusal_id=recusal.id,
        )


def test_recusal_operations_emit_audit_events(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Audit test reason",
    )

    service.resolve_recusal(
        user_id=1,
        recusal_id=recusal.id,
    )

    events = setup_j6c.execute(
        """
        SELECT event_type, actor_id, tenant_id, action
        FROM audit_events
        WHERE tenant_id = 'tenant-001'
        ORDER BY id
        """
    ).fetchall()

    event_types = [row["event_type"] for row in events]

    assert "judicial_recusal_recorded" in event_types
    assert "judicial_recusal_resolved" in event_types

    matching = [
        row
        for row in events
        if row["event_type"] in {
            "judicial_recusal_recorded",
            "judicial_recusal_resolved",
        }
    ]

    assert all(row["actor_id"] == 1 for row in matching)
    assert all(row["tenant_id"] == "tenant-001" for row in matching)


def test_proceeding_recusal_rejects_jurisdiction_mismatch(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    setup_j6c.execute(
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
            3,
            "tenant-001",
            "service",
            "tenant-001-other",
            "primary",
            "service_dispute",
            "active",
        ),
    )

    setup_j6c.execute(
        """
        UPDATE judicial_proceedings
        SET jurisdiction_id = 3
        WHERE id = 1
        """
    )
    setup_j6c.commit()

    with pytest.raises(
        ValueError,
        match="judicial proceeding jurisdiction mismatch",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.PROCEEDING,
            proceeding_id=1,
            reason="Jurisdiction mismatch",
        )

def test_proceeding_recusal_rejects_unknown_proceeding(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(
        ValueError,
        match="judicial proceeding not found",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.PROCEEDING,
            proceeding_id=999,
            reason="Unknown proceeding",
        )


def test_recusal_rejects_unknown_authority(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(
        ValueError,
        match="judicial authority not found",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=999,
            jurisdiction_id=1,
            scope=JudicialRecusalScope.JURISDICTION,
            reason="Unknown authority",
        )


def test_recusal_rejects_authority_jurisdiction_mismatch(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    with pytest.raises(
        ValueError,
        match="judicial authority jurisdiction mismatch",
    ):
        service.record_recusal(
            user_id=1,
            judicial_authority_id=1,
            jurisdiction_id=2,
            scope=JudicialRecusalScope.JURISDICTION,
            reason="Authority jurisdiction mismatch",
        )


def test_recusal_does_not_mutate_proceeding_or_dispute(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    proceeding_before = setup_j6c.execute(
        """
        SELECT status, jurisdiction_id, dispute_id, opened_by_authority_id
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    dispute_before = setup_j6c.execute(
        """
        SELECT status, service_act_id, initiator_user_id, reason
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.PROCEEDING,
        proceeding_id=1,
        reason="No mutation test",
    )

    service.resolve_recusal(
        user_id=1,
        recusal_id=1,
    )

    proceeding_after = setup_j6c.execute(
        """
        SELECT status, jurisdiction_id, dispute_id, opened_by_authority_id
        FROM judicial_proceedings
        WHERE id = 1
        """
    ).fetchone()

    dispute_after = setup_j6c.execute(
        """
        SELECT status, service_act_id, initiator_user_id, reason
        FROM disputes
        WHERE id = 1
        """
    ).fetchone()

    assert tuple(proceeding_after) == tuple(proceeding_before)
    assert tuple(dispute_after) == tuple(dispute_before)


def test_resolver_can_differ_from_recusal_initiator(setup_j6c):
    service = JudicialRecusalService(setup_j6c)

    setup_j6c.execute(
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
            2,
            "tenant-001",
            2,
            1,
            "primary",
            "test-source-2",
            "test-basis-2",
            "qualified",
            1,
            "appointed",
        ),
    )

    setup_j6c.execute(
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
            2,
            "tenant-001",
            2,
            "judge",
            1,
            "primary",
            2,
            2,
            "active",
        ),
    )

    setup_j6c.execute(
        """
        INSERT INTO judicial_conferrals (
            id,
            tenant_id,
            appointment_id,
            authority_id,
            conferring_authority,
            conferral_instrument,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            2,
            "tenant-001",
            2,
            2,
            "test-conferring-authority-2",
            "test-instrument-2",
            "active",
        ),
    )

    setup_j6c.commit()

    recusal = service.record_recusal(
        user_id=1,
        judicial_authority_id=1,
        jurisdiction_id=1,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Separate resolver test",
    )

    resolved = service.resolve_recusal(
        user_id=2,
        recusal_id=recusal.id,
    )

    assert resolved.initiated_by == 1
    assert resolved.status == JudicialRecusalStatus.RESOLVED

    event = setup_j6c.execute(
        """
        SELECT actor_id
        FROM audit_events
        WHERE event_type = 'judicial_recusal_resolved'
          AND tenant_id = 'tenant-001'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    assert event["actor_id"] == 2
