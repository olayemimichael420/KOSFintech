from types import SimpleNamespace

import bot
from services.authentication_service import AuthenticatedIdentity


def test_get_authenticated_identity_uses_application_telegram_identity_service():
    expected = AuthenticatedIdentity(
        user_id=42,
        tenant_id="tenant-001",
    )

    class FakeTelegramIdentityService:
        def __init__(self):
            self.received_update = None

        def authenticate_update(self, update):
            self.received_update = update
            return expected

    telegram_identity = FakeTelegramIdentityService()

    services = SimpleNamespace(
        telegram_identity=telegram_identity,
    )

    application = SimpleNamespace(
        bot_data={
            "services": services,
        },
    )

    context = SimpleNamespace(
        application=application,
    )

    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=123456789),
    )

    result = bot.get_authenticated_identity(update, context)

    assert result is expected
    assert telegram_identity.received_update is update
