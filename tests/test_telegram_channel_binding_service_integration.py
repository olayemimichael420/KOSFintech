from models.administration import Administration
from models.telegram_channel_binding import TelegramChannelBinding
from repositories.administration_repository import AdministrationRepository
from repositories.telegram_channel_binding_repository import (
    TelegramChannelBindingRepository,
)
from services.telegram_channel_binding_service import (
    TelegramChannelBindingService,
)


def test_service_resolves_real_active_binding(db_connection):
    administration = Administration(
        id=None,
        tenant_id="tenant-a",
        name="ABC School",
        administration_type="school",
    )

    administration = AdministrationRepository(db_connection).create(
        administration
    )

    TelegramChannelBindingRepository(db_connection).create(
        TelegramChannelBinding(
            id=None,
            provider="telegram",
            chat_id="-100123456789",
            tenant_id="tenant-a",
            administration_id=administration.id,
            binding_type="supergroup",
        )
    )

    service = TelegramChannelBindingService(
        TelegramChannelBindingRepository(db_connection)
    )

    result = service.resolve_chat("-100123456789")

    assert result is not None
    assert result.administration_id == administration.id
    assert result.tenant_id == "tenant-a"
    assert result.status == "active"
