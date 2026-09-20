import uuid

import pytest

from database import get_connection, init_db
from models.membership import Membership
from repositories.membership_repository import MembershipRepository
from services.membership_service import MembershipService


def _tenant(connection, tenant_id):
    connection.execute(
        "INSERT INTO tenants (tenant_id, status) VALUES (?, 'active')",
        (tenant_id,),
    )
    connection.commit()


def _person_and_anchor(connection, tenant_id):
    connection.execute(
        "INSERT INTO persons (name) VALUES (?)",
        ("Service Person",),
    )
    person_id = connection.execute(
        "SELECT id FROM persons WHERE name = ?",
        ("Service Person",),
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO church_anchors
            (tenant_id, name, provenance_reference)
        VALUES (?, ?, ?)
        """,
        (tenant_id, "Service Church", "service-provenance"),
    )
    church_anchor_id = connection.execute(
        """
        SELECT id
        FROM church_anchors
        WHERE tenant_id = ? AND name = ?
        """,
        (tenant_id, "Service Church"),
    ).fetchone()[0]

    connection.commit()
    return person_id, church_anchor_id


@pytest.fixture
def service():
    init_db()
    connection = get_connection()
    tenant_id = f"membership-service-{uuid.uuid4().hex}"

    try:
        _tenant(connection, tenant_id)
        person_id, church_anchor_id = _person_and_anchor(
            connection,
            tenant_id,
        )
        repository = MembershipRepository(connection)

        yield (
            MembershipService(
                repository=repository,
                tenant_id=tenant_id,
                connection=None,
                user_id=None,
            ),
            tenant_id,
            person_id,
            church_anchor_id,
        )
    finally:
        connection.close()


def test_create_and_get_membership(service):
    membership_service, tenant_id, person_id, church_anchor_id = service

    created = membership_service.create(
        Membership(
            id=None,
            tenant_id=tenant_id,
            person_id=person_id,
            church_anchor_id=church_anchor_id,
            provenance_reference="service-test",
        )
    )

    assert created.id is not None
    loaded = membership_service.get(created.id)

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.tenant_id == tenant_id
    assert loaded.person_id == person_id
    assert loaded.church_anchor_id == church_anchor_id
    assert loaded.membership_status == "active"
    assert loaded.provenance_reference == "service-test"


def test_create_rejects_tenant_mismatch(service):
    membership_service, tenant_id, person_id, church_anchor_id = service

    with pytest.raises(ValueError, match="tenant mismatch"):
        membership_service.create(
            Membership(
                id=None,
                tenant_id=f"other-{uuid.uuid4().hex}",
                person_id=person_id,
                church_anchor_id=church_anchor_id,
                provenance_reference="invalid-tenant",
            )
        )


def test_list_is_tenant_scoped(service):
    membership_service, tenant_id, person_id, church_anchor_id = service

    membership_service.create(
        Membership(
            id=None,
            tenant_id=tenant_id,
            person_id=person_id,
            church_anchor_id=church_anchor_id,
            provenance_reference="membership-one",
        )
    )

    memberships = membership_service.list()

    assert len(memberships) == 1
    assert memberships[0].tenant_id == tenant_id
    assert memberships[0].person_id == person_id
    assert memberships[0].church_anchor_id == church_anchor_id
