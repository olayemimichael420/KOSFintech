import pytest

from models.external_identity import ExternalIdentity
from repositories.external_identity_repository import ExternalIdentityRepository


def _create_user(connection, tenant_id, name="Test User"):
    cursor = connection.execute(
        """
        INSERT INTO users (
            tenant_id,
            name,
            email,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            name,
            None,
            "member",
            "active",
        ),
    )
    connection.commit()
    return cursor.lastrowid


@pytest.fixture
def connection(db_connection):
    return db_connection


def test_create_returns_identity_with_id(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    identity = ExternalIdentity(
        id=None,
        provider="telegram",
        subject="telegram-user-001",
        tenant_id="tenant-a",
        user_id=user_id,
    )

    created = repository.create(identity)

    assert created is identity
    assert created.id is not None
    assert created.provider == "telegram"
    assert created.subject == "telegram-user-001"


def test_get_returns_identity(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    created = repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="telegram-user-002",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )

    loaded = repository.get(created.id)

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.provider == "telegram"
    assert loaded.subject == "telegram-user-002"
    assert loaded.tenant_id == "tenant-a"
    assert loaded.user_id == user_id
    assert loaded.created_at is not None


def test_get_by_provider_subject_returns_canonical_binding(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="telegram-user-003",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )

    loaded = repository.get_by_provider_subject(
        "telegram",
        "telegram-user-003",
    )

    assert loaded is not None
    assert loaded.tenant_id == "tenant-a"
    assert loaded.user_id == user_id


def test_same_provider_supports_multiple_subjects(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="telegram-user-004",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )
    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="telegram-user-005",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )

    identities = repository.list_by_user("tenant-a", user_id)

    assert len(identities) == 2
    assert [item.subject for item in identities] == [
        "telegram-user-004",
        "telegram-user-005",
    ]


def test_same_subject_can_exist_for_different_providers(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="same-subject",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )
    repository.create(
        ExternalIdentity(
            id=None,
            provider="other",
            subject="same-subject",
            tenant_id="tenant-a",
            user_id=user_id,
        )
    )

    assert repository.get_by_provider_subject(
        "telegram",
        "same-subject",
    ) is not None

    assert repository.get_by_provider_subject(
        "other",
        "same-subject",
    ) is not None


def test_list_by_user_is_tenant_scoped(connection):
    tenant_a_user = _create_user(
        connection,
        "tenant-a",
        "Tenant A User",
    )
    tenant_b_user = _create_user(
        connection,
        "tenant-b",
        "Tenant B User",
    )

    repository = ExternalIdentityRepository(connection)

    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="tenant-a-user",
            tenant_id="tenant-a",
            user_id=tenant_a_user,
        )
    )
    repository.create(
        ExternalIdentity(
            id=None,
            provider="telegram",
            subject="tenant-b-user",
            tenant_id="tenant-b",
            user_id=tenant_b_user,
        )
    )

    tenant_a_identities = repository.list_by_user(
        "tenant-a",
        tenant_a_user,
    )

    assert len(tenant_a_identities) == 1
    assert tenant_a_identities[0].subject == "tenant-a-user"

    assert repository.list_by_user(
        "tenant-a",
        tenant_b_user,
    ) == []


def test_duplicate_provider_subject_is_rejected(connection):
    user_id = _create_user(connection, "tenant-a")
    repository = ExternalIdentityRepository(connection)

    identity = ExternalIdentity(
        id=None,
        provider="telegram",
        subject="duplicate-subject",
        tenant_id="tenant-a",
        user_id=user_id,
    )

    repository.create(identity)

    with pytest.raises(Exception):
        repository.create(
            ExternalIdentity(
                id=None,
                provider="telegram",
                subject="duplicate-subject",
                tenant_id="tenant-a",
                user_id=user_id,
            )
        )
