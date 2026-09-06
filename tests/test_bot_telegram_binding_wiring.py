from bot import get_telegram_binding
from services.application_service_factory import ApplicationServiceFactory
from services.application_services import ApplicationServices


class FakeChat:
    def __init__(self, chat_id):
        self.id = chat_id


class FakeUpdate:
    def __init__(self, chat_id):
        self.effective_chat = FakeChat(chat_id)


class FakeContext:
    def __init__(self, services):
        self.application = type(
            "Application",
            (),
            {"bot_data": {"services": services}},
        )()


def test_bot_uses_real_application_service_telegram_binding(
    db_connection,
):
    factory = ApplicationServiceFactory(db_connection)
    services = ApplicationServices(factory)

    assert services.telegram_channel_binding is (
        factory.build_telegram_channel_binding_service()
    )

    context = FakeContext(services)

    assert get_telegram_binding(
        FakeUpdate("-100123456789"),
        context,
    ) is None


def test_bot_resolves_real_database_telegram_binding(
    db_connection,
):
    from models.administration import Administration
    from models.telegram_channel_binding import TelegramChannelBinding
    from repositories.administration_repository import AdministrationRepository
    from repositories.telegram_channel_binding_repository import (
        TelegramChannelBindingRepository,
    )

    administration = AdministrationRepository(db_connection).create(
        Administration(
            id=None,
            tenant_id="tenant-bot-e2e",
            name="Bot E2E Administration",
            administration_type="school",
        )
    )

    TelegramChannelBindingRepository(db_connection).create(
        TelegramChannelBinding(
            id=None,
            provider="telegram",
            chat_id="-100888888888",
            tenant_id="tenant-bot-e2e",
            administration_id=administration.id,
            binding_type="operations",
        )
    )

    factory = ApplicationServiceFactory(db_connection)
    services = ApplicationServices(factory)
    context = FakeContext(services)

    binding = get_telegram_binding(
        FakeUpdate("-100888888888"),
        context,
    )

    assert binding is not None
    assert binding.chat_id == "-100888888888"
    assert binding.tenant_id == "tenant-bot-e2e"
    assert binding.administration_id == administration.id
