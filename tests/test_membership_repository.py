import sqlite3
from datetime import datetime, timezone

import pytest
import database

from models.membership import Membership
from repositories.membership_repository import MembershipRepository


def _connection(monkeypatch, tmp_path):
    db_path = tmp_path / "membership_repository.db"
    monkeypatch.setattr(database, "get_db_path", lambda: db_path)
    database.init_db()

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-a",),
    )
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        ("tenant-b",),
    )

    connection.execute(
        """
        INSERT INTO persons (name)
        VALUES (?)
        """,
        ("Person One",),
    )

    connection.execute(
        """
        INSERT INTO church_anchors
            (tenant_id, name, provenance_reference)
        VALUES (?, ?, ?)
        """,
        ("tenant-a", "Church A", "church-a-provenance"),
    )

    connection.execute(
        """
        INSERT INTO church_anchors
            (tenant_id, name, provenance_reference)
        VALUES (?, ?, ?)
        """,
        ("tenant-b", "Church B", "church-b-provenance"),
    )

    connection.commit()
    return connection


def _ids(connection):
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Person One",),
    ).fetchone()["id"]

    anchors = {
        row["tenant_id"]: row["id"]
        for row in connection.execute(
            "SELECT id, tenant_id FROM church_anchors ORDER BY id"
        ).fetchall()
    }

    return person_id, anchors


def test_create_and_get(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    person_id, anchors = _ids(connection)
    repository = MembershipRepository(connection)

    effective_from = datetime(2026, 9, 1, tzinfo=timezone.utc)
    effective_until = datetime(2027, 9, 1, tzinfo=timezone.utc)

    created = repository.create(
        Membership(
            id=None,
            tenant_id="tenant-a",
            person_id=person_id,
            church_anchor_id=anchors["tenant-a"],
            membership_status="active",
            effective_from=effective_from,
            effective_until=effective_until,
            provenance_reference="membership-test",
        )
    )

    assert created.id is not None
    assert created.tenant_id == "tenant-a"
    assert created.person_id == person_id
    assert created.church_anchor_id == anchors["tenant-a"]
    assert created.membership_status == "active"
    assert created.provenance_reference == "membership-test"

    loaded = repository.get("tenant-a", created.id)

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.tenant_id == "tenant-a"
    assert loaded.person_id == person_id
    assert loaded.church_anchor_id == anchors["tenant-a"]
    assert loaded.membership_status == "active"
    assert loaded.effective_from is not None
    assert loaded.effective_until is not None
    assert loaded.provenance_reference == "membership-test"
    assert loaded.created_at is not None

    connection.close()


def test_get_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    person_id, anchors = _ids(connection)
    repository = MembershipRepository(connection)

    created = repository.create(
        Membership(
            id=None,
            tenant_id="tenant-a",
            person_id=person_id,
            church_anchor_id=anchors["tenant-a"],
            provenance_reference="tenant-a-membership",
        )
    )

    assert repository.get("tenant-a", created.id) is not None
    assert repository.get("tenant-b", created.id) is None

    connection.close()


def test_list_is_tenant_scoped(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    person_id, anchors = _ids(connection)
    repository = MembershipRepository(connection)

    repository.create(
        Membership(
            id=None,
            tenant_id="tenant-a",
            person_id=person_id,
            church_anchor_id=anchors["tenant-a"],
            provenance_reference="membership-a1",
        )
    )
    repository.create(
        Membership(
            id=None,
            tenant_id="tenant-a",
            person_id=person_id,
            church_anchor_id=anchors["tenant-a"],
            provenance_reference="membership-a2",
        )
    )
    repository.create(
        Membership(
            id=None,
            tenant_id="tenant-b",
            person_id=person_id,
            church_anchor_id=anchors["tenant-b"],
            provenance_reference="membership-b1",
        )
    )

    memberships = repository.list("tenant-a")

    assert len(memberships) == 2
    assert all(membership.tenant_id == "tenant-a" for membership in memberships)
    assert [membership.provenance_reference for membership in memberships] == [
        "membership-a1",
        "membership-a2",
    ]

    connection.close()


def test_missing_membership_returns_none(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    repository = MembershipRepository(connection)

    assert repository.get("tenant-a", 999999) is None

    connection.close()


def test_membership_accepts_same_tenant_church_anchor(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    person_id, anchors = _ids(connection)
    repository = MembershipRepository(connection)

    created = repository.create(
        Membership(
            id=None,
            tenant_id="tenant-a",
            person_id=person_id,
            church_anchor_id=anchors["tenant-a"],
            provenance_reference="same-tenant",
        )
    )

    assert created.church_anchor_id == anchors["tenant-a"]

    connection.close()


def test_membership_rejects_cross_tenant_church_anchor(monkeypatch, tmp_path):
    connection = _connection(monkeypatch, tmp_path)
    person_id, anchors = _ids(connection)
    repository = MembershipRepository(connection)

    with pytest.raises(sqlite3.IntegrityError):
        repository.create(
            Membership(
                id=None,
                tenant_id="tenant-a",
                person_id=person_id,
                church_anchor_id=anchors["tenant-b"],
                provenance_reference="cross-tenant",
            )
        )

    connection.close()
