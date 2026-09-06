from models.administration import Administration
from models.telegram_channel_binding import TelegramChannelBinding
from models.user import User
from repositories.user_repository import UserRepository
from repositories.administration_repository import AdministrationRepository
from repositories.telegram_channel_binding_repository import (
    TelegramChannelBindingRepository,
)
from services.administration_context_service import AdministrationContextService
from services.telegram_channel_binding_service import (
    TelegramChannelBindingService,
)


def test_bound_chat_resolves_administration_context(db_connection):
    administration = Administration(
        id=None,
        tenant_id="tenant-a",
        name="ABC School",
        administration_type="school",
    )

    administration = AdministrationRepository(db_connection).create(
        administration
    )

    user = UserRepository(db_connection).create(
        User(
            id=None,
            tenant_id="tenant-a",
            name="Test User",
            email="user@example.com",
            role="member",
            status="active",
        )
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

    binding_service = TelegramChannelBindingService(
        TelegramChannelBindingRepository(db_connection)
    )
    context_service = AdministrationContextService(db_connection)

    binding = binding_service.resolve_chat("-100123456789")

    context = context_service.resolve(
        user_id=user.id,
        administration_id=binding.administration_id,
        tenant_id=binding.tenant_id,
    )

    assert context is not None
    assert context.administration_id == administration.id
    assert context.tenant_id == "tenant-a"
