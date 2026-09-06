from types import SimpleNamespace

import bot
from services.administration_context_service import AdministrationContext


def test_get_administration_context_composes_identity_binding_and_context():
    expected = AdministrationContext(
        user_id=42,
        tenant_id="tenant-001",
        administration_id=7,
    )

    class FakeTelegramIdentityService:
        def authenticate_update(self, update):
            return SimpleNamespace(
                user_id=42,
                tenant_id="tenant-001",
            )

    class FakeTelegramChannelBindingService:
        def resolve_chat(self, chat_id):
            return SimpleNamespace(
                tenant_id="tenant-001",
                administration_id=7,
            )

    class FakeAdministrationContextService:
        def __init__(self):
            self.received = None

        def resolve(self, **kwargs):
            self.received = kwargs
            return expected

    administration_context = FakeAdministrationContextService()

    services = SimpleNamespace(
        telegram_identity=FakeTelegramIdentityService(),
        telegram_channel_binding=FakeTelegramChannelBindingService(),
        administration_context=administration_context,
    )

    application = SimpleNamespace(
        bot_data={"services": services},
    )

    context = SimpleNamespace(application=application)

    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=123456789),
        effective_chat=SimpleNamespace(id=-100123456789),
    )

    result = bot.get_administration_context(update, context)

    assert result is expected
    assert administration_context.received == {
        "user_id": 42,
        "administration_id": 7,
        "tenant_id": "tenant-001",
    }
