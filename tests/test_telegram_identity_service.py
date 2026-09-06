import sqlite3

from models.external_identity import ExternalIdentity
from services.authentication_service import AuthenticatedIdentity
from services.telegram_identity_service import TelegramIdentityService


class FakeExternalIdentityService:
    def __init__(self, identity=None):
        self.identity = identity
        self.calls = []

    def resolve(self, provider, subject):
        self.calls.append((provider, subject))
        return self.identity


class FakeAuthenticationService:
    def __init__(self, identity=None):
        self.identity = identity
        self.calls = []

    def authenticate(self, user_id):
        self.calls.append(user_id)
        return self.identity


class FakeTelegramUser:
    def __init__(self, user_id):
        self.id = user_id


class FakeTelegramUpdate:
    def __init__(self, user=None):
        self.effective_user = user


def test_authenticated_telegram_identity_resolves_to_canonical_identity():
    external_identity = ExternalIdentity(
        id=1,
        provider="telegram",
        subject="123456789",
        tenant_id="tenant-001",
        user_id=42,
    )
    authenticated_identity = AuthenticatedIdentity(
        user_id=42,
        tenant_id="tenant-001",
    )

    external_service = FakeExternalIdentityService(external_identity)
    authentication_service = FakeAuthenticationService(authenticated_identity)

    service = TelegramIdentityService(
        external_identity_service=external_service,
        authentication_service=authentication_service,
    )

    result = service.authenticate_update(
        FakeTelegramUpdate(FakeTelegramUser(123456789))
    )

    assert result == authenticated_identity
    assert external_service.calls == [("telegram", "123456789")]
    assert authentication_service.calls == [42]


def test_unknown_telegram_identity_does_not_authenticate():
    external_service = FakeExternalIdentityService(identity=None)
    authentication_service = FakeAuthenticationService()

    service = TelegramIdentityService(
        external_identity_service=external_service,
        authentication_service=authentication_service,
    )

    result = service.authenticate_update(
        FakeTelegramUpdate(FakeTelegramUser(123456789))
    )

    assert result is None
    assert external_service.calls == [("telegram", "123456789")]
    assert authentication_service.calls == []


def test_inactive_canonical_user_does_not_authenticate():
    external_identity = ExternalIdentity(
        id=1,
        provider="telegram",
        subject="123456789",
        tenant_id="tenant-001",
        user_id=42,
    )

    external_service = FakeExternalIdentityService(external_identity)
    authentication_service = FakeAuthenticationService(identity=None)

    service = TelegramIdentityService(
        external_identity_service=external_service,
        authentication_service=authentication_service,
    )

    result = service.authenticate_update(
        FakeTelegramUpdate(FakeTelegramUser(123456789))
    )

    assert result is None
    assert authentication_service.calls == [42]


def test_missing_telegram_user_does_not_authenticate():
    external_service = FakeExternalIdentityService()
    authentication_service = FakeAuthenticationService()

    service = TelegramIdentityService(
        external_identity_service=external_service,
        authentication_service=authentication_service,
    )

    result = service.authenticate_update(
        FakeTelegramUpdate(user=None)
    )

    assert result is None
    assert external_service.calls == []
    assert authentication_service.calls == []


def test_telegram_identity_does_not_supply_tenant_or_authority():
    external_identity = ExternalIdentity(
        id=1,
        provider="telegram",
        subject="123456789",
        tenant_id="tenant-001",
        user_id=42,
    )
    authenticated_identity = AuthenticatedIdentity(
        user_id=42,
        tenant_id="tenant-001",
    )

    external_service = FakeExternalIdentityService(external_identity)
    authentication_service = FakeAuthenticationService(authenticated_identity)

    service = TelegramIdentityService(
        external_identity_service=external_service,
        authentication_service=authentication_service,
    )

    result = service.authenticate_update(
        FakeTelegramUpdate(FakeTelegramUser(123456789))
    )

    assert result.user_id == 42
    assert result.tenant_id == "tenant-001"
    assert not hasattr(result, "authority")
    assert not hasattr(result, "role")
    assert not hasattr(result, "permission")
