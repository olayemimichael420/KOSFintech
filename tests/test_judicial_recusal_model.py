from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from models.judicial_recusal import (
    JudicialRecusal,
    JudicialRecusalScope,
    JudicialRecusalStatus,
)


def test_judicial_recusal_defaults_to_active():
    recusal = JudicialRecusal(
        id=None,
        tenant_id="tenant-001",
        judicial_authority_id=10,
        jurisdiction_id=20,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Declared conflict requiring recusal.",
        initiated_by=30,
    )

    assert recusal.id is None
    assert recusal.tenant_id == "tenant-001"
    assert recusal.judicial_authority_id == 10
    assert recusal.jurisdiction_id == 20
    assert recusal.scope == JudicialRecusalScope.JURISDICTION
    assert recusal.proceeding_id is None
    assert recusal.status == JudicialRecusalStatus.ACTIVE
    assert recusal.recorded_at is None
    assert recusal.resolved_at is None


def test_judicial_recusal_supports_proceeding_scope():
    recusal = JudicialRecusal(
        id=1,
        tenant_id="tenant-001",
        judicial_authority_id=10,
        jurisdiction_id=20,
        scope=JudicialRecusalScope.PROCEEDING,
        proceeding_id=50,
        reason="Proceeding-specific conflict recorded.",
        initiated_by=30,
    )

    assert recusal.scope == JudicialRecusalScope.PROCEEDING
    assert recusal.proceeding_id == 50


def test_judicial_recusal_preserves_reason_and_provenance():
    recorded_at = datetime(2026, 9, 9, 12, 0, 0)

    recusal = JudicialRecusal(
        id=1,
        tenant_id="tenant-001",
        judicial_authority_id=10,
        jurisdiction_id=20,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Conflict disclosed and recorded.",
        initiated_by=30,
        recorded_at=recorded_at,
    )

    assert recusal.reason == "Conflict disclosed and recorded."
    assert recusal.initiated_by == 30
    assert recusal.recorded_at == recorded_at


def test_judicial_recusal_status_values_are_stable():
    assert JudicialRecusalStatus.ACTIVE.value == "active"
    assert JudicialRecusalStatus.RESOLVED.value == "resolved"


def test_judicial_recusal_scope_values_are_stable():
    assert JudicialRecusalScope.JURISDICTION.value == "jurisdiction"
    assert JudicialRecusalScope.PROCEEDING.value == "proceeding"


def test_judicial_recusal_is_immutable():
    recusal = JudicialRecusal(
        id=None,
        tenant_id="tenant-001",
        judicial_authority_id=10,
        jurisdiction_id=20,
        scope=JudicialRecusalScope.JURISDICTION,
        reason="Conflict recorded.",
        initiated_by=30,
    )

    with pytest.raises(FrozenInstanceError):
        recusal.id = 999
